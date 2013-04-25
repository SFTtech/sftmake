#!/usr/bin/python3

# this file is, again, part of [sft]make
#
# licensed GPLv3 or later, no warranty, gschichten.
#
# as the sftmake config language and its parsing is struggling
# in development, this is an attempt to sftmake configuration
# via the regular python language
#
# (c) 2013 [sft]technologies, jonas jelten

import re


'''
class for working with an smfile
must be superclass for any config language class

(e.g. the python pysmfile inherits from smfile)
'''
class smfile:

	def __init__(self, filename):
		self.filename = filename
		with open(self.filename) as f:
			self.content = f.read()

		#dict containing the configuration stuff:
		self.data = None

	def get_content(self):
		return self.content

	def run(self):
		raise NotImplementedError("run method must be implemented")


def smfile_factory(filepath):

	#number of lines of the smfile that will be looked at
	#to determine the config language
	headerline_count = 3

	with open(filepath) as f:
		headerlines = ""

		for i in range(headerline_count):
			headerlines += f.readline()

	#if the first line of the smfile contains "python",
	#it is written in python.
	if re.match(r"#.*python.*", headerlines):
		#python conf file

		from conf_pysmfile import pysmfile
		smfile = pysmfile(filepath)
		return smfile

	#TODO: smlang smfile
	#elif re.match(r".*smlang.*", headerlines):
	#	smlang conf file
	#	from conf_smsmfile import smsmfile
	#	smfile = smsmfile(filepath)
	#	return smfile

	else:
		raise Exception("unknown smfile file header in " + str(filepath))
