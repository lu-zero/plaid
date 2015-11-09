from __future__ import print_function
import sys
sys.path.insert(0,'..')
import os
from pprint import pprint

from flask import *

from app import *
from app.models import *
from subprocess import *


def filenames_modified(patch):
    # We need to figure out which files are touched.
    # Let's look for lines which declare a list of hunks
    filenames = []

    for line in patch.content.splitlines():
        if patch.content.startswith('diff --git a/'):
            start = len('diff --git a/')
            try:
                end = line.index(' b/')
                filenames.append(line[start:end])
            except:
                pass

    return filenames


def has_been_modified_at_this_time(filename, date, repo_dir):
    datestr = "%d-%d-%d-%d-%d-%d" % (date.year, date.month, date.day,
                                     date.hour, date.minute, date.second)
    command = 'sh commits_to_file_specific_date.sh "%s" "%s" "%s"' % (repo_dir, filename, datestr)
    try:
        output = check_output(command, shell=True, stderr=STDOUT)
        return True
    except:
        return False


def has_been_committed_with_this_message_and_author(filename, message, email, repo_dir):
    command = 'sh commits_to_file_specific_author_and_message.sh "%s" "%s" "%s" "%s"' % (repo_dir, filename, email, message)
    try:
        output = check_output(command, shell=True, stderr=STDOUT)
        return True
    except:
        return False


def is_patch_committed(patch, repo_dir):
    """
    Has this patch been committed?
    This function adopts heuristics approaches to try to figure it out.
    :param patch:
    :return:
    """

    filenames = filenames_modified(patch)

    # This works when the patch sent by e-mail is committed, instead of having a committer
    # committing from his own tree
    for f in filenames:
        if has_been_modified_at_this_time(f, patch.date, repo_dir):
            return True

    # We simply look for a commit with a specific message
    email = patch.submitter.email.replace(' at ', '@')
    msg = patch.name.strip()
    # We avoid considering messages too short (that would be risky)
    if len(msg) > 10:
        for f in filenames:
            if has_been_committed_with_this_message_and_author(f, msg, email, repo_dir):
                return True


def main():
    if len(sys.argv) != 2:
        print("One parameter is required: the path to the git repository (found %i)" % (len(sys.argv) - 1), file=sys.stderr)
        sys.exit(1)
    repo_dir = sys.argv[1]

    for p in Patch.query.all():
        if is_patch_committed(p, repo_dir):
            print("Patch committed (%s)" % p.name.strip())

if __name__ == "__main__":
    main()