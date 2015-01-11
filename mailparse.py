import datetime
import mailbox
import operator
import re

from email.header import Header
from email.header import decode_header
from email.utils import mktime_tz
from email.utils import parsedate_tz

from flask.ext.migrate import Migrate
from flask.ext.script import Manager

from app import app, db
from app.models import Comment
from app.models import Patch
from app.models import Series
from app.models import PatchState
from app.models import Project
from app.models import Submitter
from app.models import Tag
from app.parser import parse_patch


class SubjectParser(object):
    re_re = re.compile('^(re|fwd?)[:\s]\s*', re.I)
    prefix_re = re.compile('^\[([^\]]*)\]\s*(.*)$')
    split_re = re.compile('[,\s]+')

    def __init__(self, subject, drop_prefixes=None):
        self.subject = self._clean_subject(subject, drop_prefixes)
        self.tags, self.name = self._derive_tag_names(self.subject)

    def _split_prefixes(self, prefix):
        """ Turn a prefix string into a list of prefix tokens

        >>> split_prefixes('PATCH')
        ['PATCH']
        >>> split_prefixes('PATCH,RFC')
        ['PATCH', 'RFC']
        >>> split_prefixes('')
        []
        >>> split_prefixes('PATCH,')
        ['PATCH']
        >>> split_prefixes('PATCH ')
        ['PATCH']
        >>> split_prefixes('PATCH,RFC')
        ['PATCH', 'RFC']
        >>> split_prefixes('PATCH 1/2')
        ['PATCH', '1/2']
        """
        matches = self.split_re.split(prefix)
        return [s for s in matches if s != '']

    def _clean_subject(self, subject, drop_prefixes=None):
        """ Clean a Subject: header from an incoming patch.

        Removes Re: and Fwd: strings, as well as [PATCH]-style prefixes. By
        default, only [PATCH] is removed, and we keep any other bracketed data
        in the subject. If drop_prefixes is provided, remove those too,
        comparing case-insensitively.

        >>> clean_subject('meep')
        'meep'
        >>> clean_subject('Re: meep')
        'meep'
        >>> clean_subject('[PATCH] meep')
        'meep'
        >>> clean_subject('[PATCH] meep \\n meep')
        'meep meep'
        >>> clean_subject('[PATCH RFC] meep')
        '[RFC] meep'
        >>> clean_subject('[PATCH,RFC] meep')
        '[RFC] meep'
        >>> clean_subject('[PATCH,1/2] meep')
        '[1/2] meep'
        >>> clean_subject('[PATCH RFC 1/2] meep')
        '[RFC,1/2] meep'
        >>> clean_subject('[PATCH] [RFC] meep')
        '[RFC] meep'
        >>> clean_subject('[PATCH] [RFC,1/2] meep')
        '[RFC,1/2] meep'
        >>> clean_subject('[PATCH] [RFC] [1/2] meep')
        '[RFC,1/2] meep'
        >>> clean_subject('[PATCH] rewrite [a-z] regexes')
        'rewrite [a-z] regexes'
        >>> clean_subject('[PATCH] [RFC] rewrite [a-z] regexes')
        '[RFC] rewrite [a-z] regexes'
        >>> clean_subject('[foo] [bar] meep', ['foo'])
        '[bar] meep'
        >>> clean_subject('[FOO] [bar] meep', ['foo'])
        '[bar] meep'
        """

        subject = HeaderParser.clean_header(subject)

        if drop_prefixes is None:
            drop_prefixes = []
        else:
            drop_prefixes = [s.lower() for s in drop_prefixes]

        drop_prefixes.append('patch')

        # remove Re:, Fwd:, etc
        subject = self.re_re.sub(' ', subject)

        subject = normalise_space(subject)

        prefixes = []

        match = self.prefix_re.match(subject)

        while match:
            prefix_str = match.group(1)
            prefixes += [p for p in self._split_prefixes(prefix_str)
                         if p.lower() not in drop_prefixes]

            subject = match.group(2)
            match = self.prefix_re.match(subject)

        subject = normalise_space(subject)

        subject = subject.strip()
        if prefixes:
            subject = '[%s] %s' % (','.join(prefixes), subject)

        return subject

    def _derive_tag_names(self, subject):
        # skip the parts indicating the index in patchset (e.g., [1/2])
        if subject.find(']') != -1:
            index_end = subject.index(']')
            subject = subject[index_end + 1:]

        parts = subject.split(':')
        if len(parts) < 2:
            # no colon
            return [], subject

        tags = [x.strip()
                for x in parts[0:-1]
                if x.strip().find(' ') == -1]
        subject = ':'.join(parts[len(tags):])
        return tags, subject


class ContentParser(object):
    sig_re = re.compile('^(-- |_+)\n.*', re.S | re.M)
    git_re = re.compile('^The following changes since commit.*' +
                        '^are available in the git repository at:\n'
                        '^\s*([\S]+://[^\n]+)$',
                        re.DOTALL | re.MULTILINE)

    def __init__(self, project, mail):
        self.patch = None
        self.comment = ''
        self.pull_url = None
        self._find_content(project, mail)

    def _find_pull_request(self, content):
        match = self.git_re.search(content)
        if match:
            return match.group(1)
        return None

    def _clean_content(self, s):
        """ Try to remove signature (-- ) and list footer (_____) cruft """
        str = self.sig_re.sub('', s)
        return str.strip()

    def _find_content(self, project, mail):
        for part in mail.walk():
            if part.get_content_maintype() != 'text':
                continue

            payload = part.get_payload(decode=True)
            charset = part.get_content_charset()
            subtype = part.get_content_subtype()

            # if we don't have a charset, assume utf-8
            if charset is None:
                charset = 'utf-8'

            if not isinstance(payload, unicode):
                payload = unicode(payload, charset)

            if subtype in ['x-patch', 'x-diff']:
                self.patch = payload

            elif subtype == 'plain':
                c = payload

                if not self.patch:
                    (self.patch, c) = parse_patch(payload)

                if not self.pull_url:
                    self.pull_url = self._find_pull_request(payload)

                if c is not None:
                    self.comment += c.strip() + '\n'

        self.comment = self._clean_content(self.comment)


class HeaderParser(object):
    list_id_headers = ['List-ID', 'X-Mailing-List', 'X-list', 'To', 'CC']
    listid_res = [re.compile('.*<([^>]+)>.*', re.S),
                  re.compile('^([\S]+)$', re.S)]
    # tuple of (regex, fn)
    #  - where fn returns a (name, email) tuple from the match groups
    #    resulting from re.match().groups()
    from_res = [
        # for "Firstname Lastname" <example@example.com> style addresses
        (re.compile('"?(.*?)"?\s*<([^>]+)>'), (lambda g: (g[0], g[1]))),
        # for example@example.com (Firstname Lastname) style addresses
        (re.compile('"?(.*?)"?\s*\(([^\)]+)\)'), (lambda g: (g[1], g[0]))),
        # everything else
        (re.compile('(.*)'), (lambda g: (None, g[0]))),
    ]

    def __init__(self, mail):
        self.message_id = mail.get('Message-Id').strip()
        submitter = self._find_submitter_name_and_email(mail)
        self.from_name = submitter[0]
        self.from_email = submitter[1]
        self.project_name = self._find_project_name(mail)

    @staticmethod
    def clean_header(header):
        """ Decode (possibly non-ascii) headers """

        def decode(fragment):
            (frag_str, frag_encoding) = fragment
            if frag_encoding:
                return frag_str.decode(frag_encoding)
            return frag_str.decode()

        fragments = map(decode, decode_header(header))
        return normalise_space(u' '.join(fragments))

    def _find_submitter_name_and_email(self, mail):
        from_header = self.clean_header(mail.get('From'))
        (name, email) = (None, None)

        for regex, fn in self.from_res:
            match = regex.match(from_header)
            if match:
                (name, email) = fn(match.groups())
                break

        if email is None:
            raise Exception("Could not parse From: header")

        email = email.strip()
        if name is not None:
            name = name.strip()

        return (name, email)

    def _find_project_name(self, mail):
        for header in self.list_id_headers:
            if header in mail:
                for listid_re in self.listid_res:
                    match = listid_re.match(mail.get(header))
                    if match:
                        break

                if not match:
                    continue

                listid = match.group(1)
                return listid


def import_mailbox(path, project):
    mbox = mailbox.mbox(path, create=False)
    for mail in mbox:
        import_mail(mail, project)
    return None


migrate = Migrate(app, db)
manager = Manager(app)

whitespace_re = re.compile('\s+')
gitsendemail_re = re.compile("<(\d+-\d+)-(\d+)-git-send-email-(.+)")


def normalise_space(str):
    return whitespace_re.sub(' ', str).strip()


def find_project(project_name):
    if project_name:
        return Project.query.filter_by(listid=project_name).first()
    else:
        return None


def find_or_create_tags(tag_names):
    return [Tag.get_or_create(tag_name) for tag_name in tag_names]


def mail_date(mail):
    t = parsedate_tz(mail.get('Date', ''))
    if not t:
        return datetime.datetime.utcnow()
    return datetime.datetime.utcfromtimestamp(mktime_tz(t))


def mail_headers(mail):
    return reduce(operator.__concat__,
                  ['%s: %s\n' % (k, Header(v, header_name=k,
                                           continuation_ws='\t').encode())
                   for (k, v) in mail.items()])


def find_patch_for_mail(project, mail):
    # construct a list of possible reply message ids
    refs = []
    if 'In-Reply-To' in mail:
        refs.append(mail.get('In-Reply-To'))

    if 'References' in mail:
        rs = mail.get('References').split()
        rs.reverse()
        for r in rs:
            if r not in refs:
                refs.append(r)

    patch = None
    for ref in refs:
        # first, check for a direct reply
        patch = Patch.query.filter_by(project=project, msgid=ref).first()

        # see if we have comments that refer to a patch
        if not patch:
            comment = Comment.query.filter_by(msgid=ref).first()
            if comment:
                return comment.patch

    return patch


def dump_mail(mail, message_id):
    import os
    try:
        os.mkdir('rej/')
    except:
        pass
    with open('rej/' + message_id, 'w') as f:
        f.write(str(mail))


def find_ancestor(project, mail, patch):
    ancestor = find_patch_for_mail(project, mail)

    if ancestor and ancestor.series != patch.series:
        return ancestor

    return None


def import_mail(mail, project_name=None):
    # some basic sanity checks
    if 'From' not in mail:
        return 0

    if 'Subject' not in mail:
        return 0

    if 'Message-Id' not in mail:
        return 0

    hint = mail.get('X-Patchwork-Hint', '').lower()
    if hint == 'ignore':
        return 0

    header_parser = HeaderParser(mail)
    submitter = Submitter.get_or_create(name=header_parser.from_name,
                                        email=header_parser.from_email)

    if not project_name:
        project_name = header_parser.project_name

    project = find_project(project_name)
    if project is None:
        print 'No project for %s found' % header_parser.project_name
        dump_mail(mail, header_parser.message_id)
        return 0
    try:
        content_parser = ContentParser(project, mail)
    except:
        print 'Email %s is not parsable' % (header_parser.message_id)
        dump_mail(mail, header_parser.message_id)
        return 0

    patch = None
    if content_parser.pull_url or content_parser.patch:
        subject_parser = SubjectParser(mail.get('Subject'),
                                       [project.linkname])
        name = subject_parser.name
        tags = find_or_create_tags(subject_parser.tags)
        patch = Patch(name=name, pull_url=content_parser.pull_url,
                      content=content_parser.patch, date=mail_date(mail),
                      headers=mail_headers(mail), tags=tags)

        match = gitsendemail_re.match(header_parser.message_id)
        if match:
            (uid, num, email) = match.groups()
            series = Series.get_or_create(uid)
        else:
            series = Series.get_or_create(header_parser.message_id)

        series.patches.append(patch)
        db.session.add(series)

        patch.submitter = submitter
        patch.msgid = header_parser.message_id
        patch.project = project
        ancestor = find_ancestor(project, mail, patch)
        if ancestor:
            patch.ancestors.append(ancestor)

    if patch is None:
        patch = find_patch_for_mail(project, mail)
        if patch is not None:
            patch.state = PatchState.comments

    if patch is not None:
        db.session.add(patch)

    if content_parser.comment and patch is not None:
        comment = Comment(patch=patch, date=mail_date(mail),
                          content=content_parser.comment,
                          headers=mail_headers(mail))
        comment.submitter = submitter
        comment.msgid = header_parser.message_id

        db.session.add(comment)

    db.session.commit()
    return 0


if __name__ == '__main__':
    manager.run()
