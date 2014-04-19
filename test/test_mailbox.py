import datetime
import email
import mailbox
import unittest

from mailparse import find_project_name
from mailparse import find_submitter
from mailparse import mail_date


class TestMailbox(unittest.TestCase):
    libavmbox = mailbox.mbox('test/data/livav_1_99.mbox')
    email1 = email.message_from_file(open('test/data/someemails/1.eml'))
    email2 = email.message_from_file(open('test/data/someemails/2.eml'))

    def test_find_submitter(self):
        submitter1 = find_submitter(self.email1)
        self.assertEqual(u'Ramiro Polla', submitter1.name)
        self.assertEqual(u'ramiro.polla@gmail.com', submitter1.email)
        submitter2 = find_submitter(self.email2)
        self.assertEqual(u'M\xe5ns Rullg\xe5rd', submitter2.name)
        self.assertEqual(u'mans@mansr.com', submitter2.email)

    def test_find_project_name(self):
        self.assertEqual('libav-devel.libav.org',
                         find_project_name(self.email1))
        self.assertEqual('libav-devel.libav.org',
                         find_project_name(self.email2))

    def test_mail_date(self):
        # 2011-03-16 18:37:31
        d1 = datetime.datetime.strptime('2011-03-16 18:37:31',
                                        "%Y-%m-%d %H:%M:%S")
        self.assertEqual(d1, mail_date(self.email1))
        # 2011-03-16 18:53:16
        d2 = datetime.datetime.strptime('2011-03-16 18:53:16',
                                        "%Y-%m-%d %H:%M:%S")
        self.assertEqual(d2, mail_date(self.email2))
