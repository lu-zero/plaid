import datetime
import email
import unittest

from mailparse import HeaderParser
from mailparse import mail_date


class TestMailbox(unittest.TestCase):
    email1 = email.message_from_file(open('test/data/someemails/1.eml'))
    email2 = email.message_from_file(open('test/data/someemails/2.eml'))

    def test_submitter(self):
        header = HeaderParser(self.email1)
        self.assertEqual(u'Ramiro Polla', header.from_name)
        self.assertEqual(u'ramiro.polla@gmail.com', header.from_email)
        header = HeaderParser(self.email2)
        self.assertEqual(u'M\xe5ns Rullg\xe5rd', header.from_name)
        self.assertEqual(u'mans@mansr.com', header.from_email)

    def test_project_name(self):
        header = HeaderParser(self.email1)
        self.assertEqual('libav-devel.libav.org',
                         header.project_name)
        header = HeaderParser(self.email2)
        self.assertEqual('libav-devel.libav.org',
                         header.project_name)

    def test_mail_date(self):
        # 2011-03-16 18:37:31
        d1 = datetime.datetime.strptime('2011-03-16 18:37:31',
                                        "%Y-%m-%d %H:%M:%S")
        self.assertEqual(d1, mail_date(self.email1))
        # 2011-03-16 18:53:16
        d2 = datetime.datetime.strptime('2011-03-16 18:53:16',
                                        "%Y-%m-%d %H:%M:%S")
        self.assertEqual(d2, mail_date(self.email2))

    def test_ancestor(self):
        pass
