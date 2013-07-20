#!/usr/bin/env python3
#
# This file is part of sftmake.
#
# License: GPLv3 or later, no warranty, etc
#
#
# Utility functions for handling gcc -MD stuff
#
#

import re


def parse_dfile(filename):
	'''parse a gcc -MD .d file and return a list of dependency header filenames'''
	try:
		with open(filename, 'r') as f:
			content = f.readlines() #list of line, including a trailing \\n (sic)
			dependencies = list()
			for l in content:
				dependencies += clean_dfile_line(l)

			return dependencies
	except IOError as e:
		raise Exception(str(e) + " -> parsing dependency header failed")


def clean_dfile_line(line):
	'''converts a .dfile line to a list of header dependencies'''
	hmatch = re.compile(r"[-\w/\.]+\.(h|hpp)") #matches a single header file
	parts = re.split(r"\s+", line)

	#return all matching header files as list
	return filter(lambda part: hmatch.match(part), parts)
#	return [ part for part in parts if hmatch.match(part) ]

def md_enabled(ad):
	'''option interpreter, is gcc -MD enabled?'''

	if ad == "MD" or len(ad) == 0:
		return True
	elif ad == "no" or ad == "disable" or ad == "nope":
		return False
	else:
		raise Exception(repr(element) + ": unknow autodetection mode: '" + ad + "'")
