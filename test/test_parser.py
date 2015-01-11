import unittest
from app.parser import parse_patch
from mailparse import SubjectParser


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
