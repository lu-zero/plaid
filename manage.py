import sys
import traceback

from email import message_from_file

from flask.ext.script import Manager, Command, Option
from flask.ext.script.commands import InvalidCommand
from flask.ext.migrate import Migrate, MigrateCommand

from app import app
from app import db
from app.models import Role
from app.models import User
from app.models import Project

from mailparse import import_mail
from mailparse import import_mailbox


class CreateProject(Command):
    """Create a new project"""
    option_list = (
        Option('--name', '-n', required=True, dest='name', type=unicode,
               help="Set the project name to NAME."),
        Option('--listid', '-i', required=True, dest='listid', type=unicode,
               help="Set the project listid to LISTID."),
        Option('--linkname', '-l', required=True, dest="linkname",
               type=unicode,
               help="Set the project linkname to LINKNAME."),
        Option('--description', '-d', required=True, dest='description',
               type=unicode,
               help="Set the project description to DESCRIPTION."),
    )

    def run(self, name, listid, linkname, description):
        p = Project(name=name, listid=listid, linkname=linkname,
                    description=description)
        db.session.add(p)
        db.session.commit()


class CreateUser(Command):
    """Create a new user account"""
    option_list = (
        Option('--name', '-n', required=False, dest='name', type=unicode,
               help="Set the user name to NAME."),
        Option('--email', '-e', required=True, dest='email', type=unicode,
               help="Set the user's email address to EMAIL."),
        Option('--password', '-p', required=True, dest="password",
               type=unicode,
               help="Set the user's password to PASSWORD."),
        Option('--role', '-r', required=False, dest="role", default="user",
               type=unicode,
               help="Role (admin, maintainer)")
    )

    def run(self, name, email, password, role):
        u = User(name=name,
                 password=password,
                 email=email)
        try:
            u.role = getattr(Role, role)
        except:
            raise InvalidCommand("The role %s is not supported." % (role))

        print('Creating user %s' % u)
        db.session.add(u)
        db.session.commit()


class ImportMails(Command):
    """Import projects data from a mailing list or a mailbox"""

    option_list = (
        Option('--mailbox', '-m', dest='mailbox'),
        Option('--project', '-p', dest='project',
               help="Override the project"),
    )

    def import_mail_from_stdin(self, project):
        mail = message_from_file(sys.stdin)
        import_mail(mail, project)

    def run(self, mailbox, project):
        if mailbox:
            try:
                import_mailbox(mailbox, project)
            except Exception as e:
                traceback.print_exc(e)
        else:
            self.import_mail_from_stdin(project)

migrate = Migrate(app, db)

manager = Manager(app)
user_manager = Manager(usage="Create/Edit/Drop users")
user_manager.add_command('create', CreateUser())


@user_manager.command
def drop(name):
    "Drop the user from the database"
    u = User.query.filter_by(name=name).first()
    db.session.delete(u)
    db.session.commit()


@user_manager.command
def list():
    "List all the users"
    print("{0:12} {1:16} {2:5}".format("Name", "Email", "Role"))
    for u in User.query.all():
        print("{0:12} {1:16} {2:5}".format(u.name, u.email, u.role))

project_manager = Manager(usage="Create/Edit/Drop projects")
project_manager.add_command('create', CreateProject())


@project_manager.command
def drop(name):
    "Drop the project from the database"
    p = Project.query.filter_by(name=name).first()
    db.session.delete(p)
    db.session.commit()


@project_manager.command
def list():
    "List all the projects"
    print("{0:12} {1:30} {2:10}".format("Name", "List-Id", "Maintainers"))
    for p in Project.query.all():
        print("{0:12} {1:30} {2:10}".format(p.name, p.listid, p.maintainers))


@project_manager.option('-a', '--add', dest='add', default='',
                        help="Set the users as project maintainers")
@project_manager.option('-r', '--remove', dest='remove', default='',
                        help="Remove the users as project mantainers")
@project_manager.command
def maintainer(name, **kwargs):
    "Manage project maintainers"
    p = Project.query.filter_by(name=name).first()
    add = (name for name in kwargs['add'].split(',') if name)
    for name in add:
        u = User.query.filter_by(name=name).first()
        if not u:
            raise InvalidCommand("Cannot add %s: user not exists" % (name))
        try:
            p.maintainers.append(u)
        except:
            pass
    remove = (name for name in kwargs['remove'].split(',') if name)
    for name in remove:
        u = User.query.filter_by(name=name).first()
        if not u:
            raise InvalidCommand("Cannot remove %s: user not exists" % (name))
        try:
            p.maintainers.remove(u)
        except:
            pass
    db.session.commit()

manager.add_command('db', MigrateCommand)
manager.add_command('user', user_manager)
manager.add_command('project', project_manager)
manager.add_command('import', ImportMails())

if __name__ == '__main__':
    manager.run()
