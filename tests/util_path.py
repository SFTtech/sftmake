#!/usr/bin/env python

import util.path
import os.path

from logger.levels import *


def testcase(inp, ssmroot, expected, function, norm=True):

	util.path.set_smroot(ssmroot)

	message("testing " + str(function) + ", smroot = " + ssmroot)
	message("input = " + inp)

	result = function(inp)

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
	ok = ok and testcase("./subdir/myfile.lol", "./subdir", "./subdir/myfile.lol", util.path.abspath)
	ok = ok and testcase("./subdir/myfile.lol", "./subdir", "^/myfile.lol", util.path.smpath)
	ok = ok and testcase("./myfile.lol", ".", "./myfile.lol", util.path.abspath)
	ok = ok and testcase("./myfile.lol", ".", "^/myfile.lol", util.path.smpath)
	ok = ok and testcase("./f/ie", "./f", "./ie", util.path.relpath)
	ok = ok and testcase("^/ie", "./f", "./f/ie", util.path.abspath)
	ok = ok and testcase("^/ie", "./f", "ie", util.path.relpath)

	ok = ok and testcase("./f/ie", "./f", True, util.path.in_smdir, norm=False)
	ok = ok and testcase("^/ie", "./f", True, util.path.in_smdir, norm=False)
	ok = ok and testcase("^/f/ie", "./f", True, util.path.in_smdir, norm=False)

	ok = ok and testcase("/i/e", "./f", False, util.path.in_smdir, norm=False)
	ok = ok and testcase("^/../e", "./f", False, util.path.in_smdir, norm=False)
	ok = ok and testcase("../f", "./f", False, util.path.in_smdir, norm=False)

	message("path tests were " + str(ok))
	return ok
