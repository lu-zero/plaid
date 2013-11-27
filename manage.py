from flask.ext.script import Manager, Command, Option
from flask.ext.migrate import Migrate, MigrateCommand

from app import app, db

import traceback

from mailparse import *

class ImportMails(Command):

    option_list = (
        Option('--mailbox', '-m', dest='mailbox'),
    )

    def import_mail_from_stdin():
        mail = message_from_file(sys.stdin)
        import_mail(mail)

    def run(self, mailbox):
        if mailbox:
            try:
                import_mailbox(mailbox)
            except Exception as e:
                traceback.print_exc(e)
        else:
            import_mail_from_stdin()

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('import', ImportMails())

if __name__ == '__main__':
    manager.run()
