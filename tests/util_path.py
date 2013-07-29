#!/usr/bin/env python

from util.path import set_smroot, smpath, relpath, abspath, in_smdir
import os.path

from logger.levels import *

def testcase(function, inp, ssmroot, expected, rel="^", norm=True):

	set_smroot(ssmroot)

	if rel == "^":
		reltxt = ""
	else:
		reltxt = ", relative base = " + rel

	message("testing " + str(function) + ", smroot = " + ssmroot + reltxt)
	message("input = " + inp)

	if rel == "^":
		result = function(inp)
	else:
		result = function(inp, relto=rel)

	message("expected = " + str(expected))
	message("result   = " + str(result))

	if norm:
		ne = os.path.normpath(expected)
		nr = os.path.normpath(result)

	else:
		ne = expected
		nr = result

	if ne == nr:
		important("--> WIN!")
		return True
	else:
		important("--> FAIL.")
		return False


def run():
	ok = True
	ok = ok and testcase(smpath, "^/myfile.lol", ".", "^/myfile.lol")
	ok = ok and testcase(smpath, "myfile.lol", ".", "^/myfile.lol")
	ok = ok and testcase(abspath, "^/myfile.lol", ".", "myfile.lol")
	ok = ok and testcase(abspath, "myfile.lol", ".", "myfile.lol")

	ok = ok and testcase(in_smdir, "./f/ie", "./f", True, norm=False)
	ok = ok and testcase(in_smdir, "^/ie", "./f", True, norm=False)
	ok = ok and testcase(in_smdir, "^/f/ie", "./f", True, norm=False)
	ok = ok and testcase(in_smdir, "/i/e", "./f", False, norm=False)
	ok = ok and testcase(in_smdir, "^/../e", "./f", False, norm=False)
	ok = ok and testcase(in_smdir, "../f", "./f", False, norm=False)

	message("path tests were " + str(ok))
	return ok
