from app import db
from datetime import date, datetime
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
    id       = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(128), index = True)
    email    = db.Column(db.String(120), index = True, unique = True)
    role     = db.Column(db.SmallInteger, default = ROLE_USER)
    password = db.Column(db.String(64))

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
        if self.nickname:
            return self.nickname
        else:
            return self.email

    @staticmethod
    def get_by_id(userid):
        return db.session.query(User).filter_by(id=userid).first()

class Submitter(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(128), index = True)
    email = db.Column(db.String(120), index = True, unique = True)

    # Required for administrative interface
    def __unicode__(self):
        if not self.name:
            return  "<" + self.email + ">"
        return self.name + "<" + self.email + ">"

    def __init__(self, name, email):
        self.name  = name
        self.email = email

    @classmethod
    def get_or_create(self, name, email):
        instance = self.query.filter_by(email=email).first()
        if not instance:
            instance = Submitter(name=name, email=email)
            db.session.add(instance)
            db.session.commit()
        return instance


class Project(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    linkname = db.Column(db.String(128))
    name = db.Column(db.String(128))
    listid = db.Column(db.String(128),unique=True)
    listemail = db.Column(db.String(128))
    web_url = db.Column(db.String(128))
    scm_url = db.Column(db.String(128))
    webscm_url = db.Column(db.String(128))
    notifications = db.Column(db.Boolean())

    def __unicode__(self):
        return self.name

    @staticmethod
    def get_all():
        return Project.query.all()

class EmailMixin(object):
    msgid   = db.Column(db.String(255))
    name    = db.Column(db.String(255))
    date    = db.Column(db.DateTime(), default=datetime.now)
    headers = db.Column(db.Text)
    content = db.Column(db.Text)

    def __unicode__(self):
        return self.name

class Patch(EmailMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('submitter.id'))
    submitter = db.relationship('Submitter', backref='patches')
    pull_url = db.Column(db.String(255))
    commit_ref = db.Column(db.String(255))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship('Project', backref='patches')
    ancestor_id = db.Column(db.Integer, db.ForeignKey('patch.id'))
    ancestor = db.relationship('Patch', backref="successor", remote_side=[id])

    def filename(self):
        fname_re = re.compile('[^-_A-Za-z0-9\.]+')
        str = fname_re.sub('-', self.name)
        return str.strip('-') + '.patch'

    def __init__(self, name, pull_url, content, date, headers):
        self.name = name
        self.pull_url = pull_url
        self.content = content
        self.date = date
        self.headers = headers

class Comment(EmailMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('submitter.id'))
    submitter = db.relationship('Submitter', backref='comments')
    patch_id = db.Column(db.Integer, db.ForeignKey('patch.id'))
    patch = db.relationship('Patch', backref='comments')

patches = db.Table('roles',
    db.Column('serie_id', db.Integer, db.ForeignKey('serie.id')),
    db.Column('patch_id', db.Integer, db.ForeignKey('patch.id')),
)

class Serie(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255))
    uid  = db.Column(db.String(255), unique=True, nullable=True)
    date = db.Column(db.DateTime(), default=datetime.now)
    patches = db.relationship("Patch", secondary=patches, backref="series")

    @classmethod
    def get_or_create(self, uid, name=None):
        instance = self.query.filter_by(uid=uid).first()
        if not instance:
            if not name:
                name = "git-send-email-" + uid
            instance = Serie(name=name, uid=uid)
            db.session.add(instance)
            db.session.commit()
        return instance


topics = db.Table('topics',
    db.Column('patch_id', db.Integer, db.ForeignKey('patch.id')),
    db.Column('topic.id', db.Integer, db.ForeignKey('topic.id')),
)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255))
    patches = db.relationship("Patch", secondary=topics, backref="topics")


tags = db.Table('tags',
    db.Column('patch_id', db.Integer, db.ForeignKey('patch.id')),
    db.Column('tag.id', db.Integer, db.ForeignKey('tag.id')),
)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255))
    patches = db.relationship("Patch", secondary=tags, backref="tags")

