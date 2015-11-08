import re

from datetime import datetime
from datetime import timedelta
from flask.ext.security import RoleMixin
from flask.ext.security import UserMixin

import flask.ext.whooshalchemy

from sqlalchemy.orm import backref
from sqlalchemy.sql import or_
from sqlalchemy.ext.hybrid import hybrid_property

from app import db
from app.enum import DeclEnum

from flask.ext.security.utils import verify_password


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(),
                                 db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(),
                                 db.ForeignKey('role.id')))


class Role(RoleMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean(), nullable=False, default=False)
    name = db.Column(db.String(50), nullable=False, unique=True)
    github_username = db.Column(db.String(50), nullable=True, unique=True)
    email = db.Column(db.String(255), nullable=False, index=True, unique=True)
    confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255), nullable=False, default='')
    reset_password_token = db.Column(db.String(100), nullable=False,
                                     default='')
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return "<" + self.email + ">"

    def __repr__(self):
        return '<User %r>' % (self.email)

    def get_name(self):
        return self.name

    @staticmethod
    def get_by_id(userid):
        return db.session.query(User).filter_by(id=userid).first()

    @staticmethod
    def get_by_name(user_name):
        return db.session.query(User).filter_by(name=user_name).first()

    @staticmethod
    def get_by_email(email):
        return db.session.query(User).filter_by(email=email).first()

    @staticmethod
    def get_by_github_username(github_username):
        return db.session.query(User).filter_by(github_username=github_username).first()

    def is_valid_password(self, password):
        return verify_password(password, self.password)


class Submitter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    email = db.Column(db.String(120), index=True, unique=True)

    # Required for administrative interface
    def __unicode__(self):
        if not self.name:
            return "<" + self.email + ">"
        return self.name + "<" + self.email + ">"

    def __init__(self, name, email):
        self.name = name
        self.email = email

    @classmethod
    def get_or_create(self, name, email):
        instance = self.query.filter_by(email=email).first()
        if not instance:
            instance = Submitter(name=name, email=email)
            db.session.add(instance)
            db.session.commit()
        return instance


project_maintainers = db.Table('project_maintainers',
                               db.Column('id', db.Integer(), primary_key=True),
                               db.Column('user_id', db.Integer(),
                                         db.ForeignKey('user.id',
                                                       ondelete='CASCADE')),
                               db.Column('project_id', db.Integer(),
                                         db.ForeignKey('project.id',
                                                       ondelete='CASCADE')))


class PatchState(DeclEnum):
    unreviewed = "U", "Unreviewed"
    comments = "C", "Comments"
    accepted = "A", "Accepted"
    rejected = "R", "Rejected"


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    linkname = db.Column(db.String(128))
    name = db.Column(db.String(128))
    listid = db.Column(db.String(128), unique=True)
    listemail = db.Column(db.String(128))
    web_url = db.Column(db.String(128))
    scm_url = db.Column(db.String(128))
    webscm_url = db.Column(db.String(128))
    description = db.Column(db.String(256))
    notifications = db.Column(db.Boolean())
    maintainers = db.relationship('User', secondary=project_maintainers,
                                  backref=backref('projects', lazy='dynamic'),
                                  lazy='dynamic')

    def __unicode__(self):
        return self.name

    @hybrid_property
    def current_patches(self):
        return self.patches.filter(~Patch.successors.any())

    @hybrid_property
    def unreviewed_patches(self):
        q = self.current_patches
        return q.filter_by(state=PatchState.unreviewed)

    @hybrid_property
    def pending_patches(self):
        q = self.current_patches
        return q.filter(or_(Patch.state == PatchState.unreviewed,
                            Patch.state == PatchState.comments))

    @hybrid_property
    def new_patches(self):
        q = self.unreviewed_patches
        return q.filter(Patch.date > datetime.now() - timedelta(days=5))

    @hybrid_property
    def reviewed_patches(self):
        q = self.current_patches
        return q.filter_by(state=PatchState.comments)

    @hybrid_property
    def stale_patches(self):
        q = self.pending_patches
        return q.filter(Patch.date < datetime.now() - timedelta(days=20))

    @hybrid_property
    def committed_patches(self):
        q = self.current_patches
        return q.filter_by(state=PatchState.accepted)

    @hybrid_property
    def tags(self):
        return Tag.query.join(tags).join(Patch).filter_by(project_id=self.id)

    @property
    def submitters(self):
        return Submitter.query.filter(Submitter.patches.any(project_id=self.id))

    @staticmethod
    def get_all():
        return Project.query.all()


class EmailMixin(object):
    msgid = db.Column(db.String(255))
    name = db.Column(db.String(255))
    date = db.Column(db.DateTime(), default=datetime.now)
    headers = db.Column(db.Text)
    content = db.Column(db.Text)

    def __unicode__(self):
        return self.name

ancestry = db.Table('ancestry',
                    db.Column('successor_id', db.Integer,
                              db.ForeignKey('patch.id')),
                    db.Column('ancestor_id', db.Integer,
                              db.ForeignKey('patch.id')))


class Patch(EmailMixin, db.Model):
    __searchable__ = ['name', 'content']
    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('submitter.id'))
    submitter = db.relationship('Submitter', backref=backref('patches', lazy='dynamic'))
    pull_url = db.Column(db.String(255))
    commit_ref = db.Column(db.String(255), default=None)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship('Project',
                              backref=backref('patches', lazy='dynamic'))
    successors = db.relationship('Patch', backref="ancestors",
                                 secondary=ancestry,
                                 primaryjoin=ancestry.c.successor_id == id,
                                 secondaryjoin=ancestry.c.ancestor_id == id)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'))
    series = db.relationship('Series', backref=backref('patches', lazy='dynamic'))
    state = db.Column(PatchState.db_type(), default=PatchState.unreviewed)

    def filename(self):
        fname_re = re.compile('[^-_A-Za-z0-9\.]+')
        str = fname_re.sub('-', self.name)
        return str.strip('-') + '.patch'

    @property
    def description(self):
        if self.comments and self.comments[0].msgid == self.msgid:
            return self.comments[0]
        return None

    @property
    def mbox(self):
        from email.mime.nonmultipart import MIMENonMultipart
        from email.encoders import encode_7or8bit

        body = ''
        if self.description:
            body += self.description.content + '\n'
        body += self.content

        mbox = MIMENonMultipart('text', 'plain', charset='utf-8')

        mbox['Subject'] = ": ".join([t.name for t in self.tags] + [self.name.strip().capitalize()])
        mbox['From'] = '%s <%s>' % (self.submitter.name, self.submitter.email)
        mbox['Message-Id'] = self.msgid

        mbox.set_payload(body.encode('utf-8'))
        encode_7or8bit(mbox)

        return mbox.as_string()

    def __init__(self, name, pull_url, content, date, headers, tags):
        self.name = name
        self.pull_url = pull_url
        self.content = content
        self.date = date
        self.headers = headers
        self.tags = tags


class Comment(EmailMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('submitter.id'))
    submitter = db.relationship('Submitter', backref='comments')
    patch_id = db.Column(db.Integer, db.ForeignKey('patch.id'))
    patch = db.relationship('Patch', backref='comments',
                            order_by='Comment.date')


class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    uid = db.Column(db.String(255), unique=True, nullable=True)
    date = db.Column(db.DateTime(), default=datetime.now)

    @property
    def tags(self):
        return Tag.query.filter(Tag.patches.any(series_id=self.id)).all()

    @classmethod
    def get_or_create(cls, uid, name=None):
        instance = cls.query.filter_by(uid=uid).first()
        if not instance:
            if not name:
                name = "git-send-email-" + uid
            instance = Series(name=name, uid=uid)
            db.session.add(instance)
            db.session.commit()
        return instance


topics = db.Table('topics',
                  db.Column('patch_id', db.Integer, db.ForeignKey('patch.id')),
                  db.Column('topic.id', db.Integer, db.ForeignKey('topic.id')))


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    patches = db.relationship("Patch", secondary=topics, backref="topics")


tags = db.Table('tags',
                db.Column('patch_id', db.Integer, db.ForeignKey('patch.id')),
                db.Column('tag.id', db.Integer, db.ForeignKey('tag.id')))


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    patches = db.relationship("Patch", secondary=tags, backref="tags",
                              lazy="dynamic")

    @classmethod
    def get_or_create(cls, name):
        instance = cls.query.filter_by(name=name).first()
        if not instance:
            instance = Tag(name=name)
            db.session.add(instance)
            db.session.commit()
        return instance
