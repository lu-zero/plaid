# coding: UTF-8

import unittest
from app.parser import parse_patch
from mailparse import SubjectParser, parse_from_header


class TestParser(unittest.TestCase):
    comment_before_patch = """I send you my beautiful patch.
                     I hope you like it

--- a/app/models.py
+++ b/app/models.py
@@ -33,6 +33,10 @@ class User(db.Model):
     def __repr__(self):
         return '<User %r>' % (self.email)

+    @staticmethod
+    def get_by_id(userid):
+        return db.session.query(User).filter_by(id=userid).first()
+
 class Submitter(db.Model):
     id = db.Column(db.Integer, primary_key = True)
     name = db.Column(db.String(128), index = True)"""

    comment_after_patch = """
--- a/app/models.py
+++ b/app/models.py
@@ -33,6 +33,10 @@ class User(db.Model):
     def __repr__(self):
         return '<User %r>' % (self.email)

+    @staticmethod
+    def get_by_id(userid):
+        return db.session.query(User).filter_by(id=userid).first()
+
 class Submitter(db.Model):
     id = db.Column(db.Integer, primary_key = True)
     name = db.Column(db.String(128), index = True)

        Nice patch, eh?"""

    patch = """--- a/app/models.py
+++ b/app/models.py
@@ -33,6 +33,10 @@ class User(db.Model):
     def __repr__(self):
         return '<User %r>' % (self.email)

+    @staticmethod
+    def get_by_id(userid):
+        return db.session.query(User).filter_by(id=userid).first()
+
 class Submitter(db.Model):
     id = db.Column(db.Integer, primary_key = True)
     name = db.Column(db.String(128), index = True)
"""

    def setUp(self):
        pass

    def test_parse_patch_before_patch(self):
        (patch, comment) = parse_patch(self.comment_after_patch)
        self.assertEqual(self.patch, patch)

    def test_parse_patch_after_patch(self):
        (patch, comment) = parse_patch(self.comment_before_patch)
        self.assertEqual(self.patch, patch)

    def test_parse_comment_before_patch(self):
        (patch, comment) = parse_patch(self.comment_before_patch)
        self.assertEqual("""I send you my beautiful patch.
                     I hope you like it""", comment.strip())

    def test_parse_comment_after_patch(self):
        (patch, comment) = parse_patch(self.comment_after_patch)
        self.assertEqual("""Nice patch, eh?""", comment.strip())

    def test_derive_tag_names(self):
        subject_parser = SubjectParser("a: b: subject", [""])
        self.assertEqual(['a', 'b'], subject_parser.tags)
        subject_parser = SubjectParser("[1/2]a: b: subject", [""])
        self.assertEqual(['a', 'b'], subject_parser.tags)
        subject_parser = SubjectParser("[WIP]a: b: subject ", [""])
        self.assertEqual(['a', 'b'], subject_parser.tags)

    def test_parse_from_header_with_ascii_characters(self):
        self.assertEqual(("Luca Barbato", "lu_zero at gentoo.org"), parse_from_header("lu_zero at gentoo.org (Luca Barbato)"))
        self.assertEqual(("Vittorio Giovara", "vittorio.giovara at gmail.com"), parse_from_header("vittorio.giovara at gmail.com (Vittorio Giovara)"))

    def test_parse_from_header_with_UTF8(self):
        self.assertEqual((u"Alexandra Hájková", "alexandra.khirnova at gmail.com"), parse_from_header("alexandra.khirnova at gmail.com (=?UTF-8?q?Alexandra=20H=C3=A1jkov=C3=A1?=)"))
        self.assertEqual((u"Arttu Ylä-Outinen", "arttu.yla-outinen at tut.fi"), parse_from_header("arttu.yla-outinen at tut.fi (=?UTF-8?Q?Arttu_Yl=c3=a4-Outinen?=)"))

    def test_parse_from_header_with_Latin1(self):
        self.assertEqual((u"Martin Storsjö", "martin at martin.st"), parse_from_header("martin at martin.st (=?ISO-8859-15?Q?Martin_Storsj=F6?=)"))
