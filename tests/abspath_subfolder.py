#!/usr/bin/env python

import util.path
import os.path

from logger.levels import *


def testcase(inp, ssmroot, expected, function):

	util.path.set_smroot(ssmroot)

	message("testing " + str(function) + ", smroot = " + ssmroot)
	message("input = " + inp)

	result = function(inp)

	message("expected = " + expected)
	message("result   = " + result)

	ne = os.path.normpath(expected)
	nr = os.path.normpath(result)

	if ne == nr:
		important("--> WIN!")
	else:
		important("--> FAIL.")


testcase("./subdir/myfile.lol", "./subdir", "./subdir/myfile.lol", util.path.abspath)

testcase("./subdir/myfile.lol", "./subdir", "^/myfile.lol", util.path.smpath)

testcase("./myfile.lol", ".", "./myfile.lol", util.path.abspath)

testcase("./myfile.lol", ".", "^/myfile.lol", util.path.smpath)
