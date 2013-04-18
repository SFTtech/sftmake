#!/usr/bin/python3

# this file is, again, part of [sft]make
#
# licensed GPLv3 or later, no warranty, gschichten.
#
# as the sftmake config language and it's parsing is struggling
# in it's development, this is an attempt to configure sftmake
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

	def get_content(self):
		return self.content

	def run(self):
		raise NotImplementedError("run method must be implemented")


def smfile_factory(filepath):

	with open(filepath) as f:
		firstline = f.readline()

	#if the first line of the smfile contains "python",
	#it is written in python.
	if re.match(r"#.*python.*", firstline):
		#python conf file

		from conf_pysmfile import pysmfile
		smfile = pysmfile(filepath)
		return smfile

	#elif: #TODO: smlang smfile

	else:
		raise Exception("unknown config file header")
		#smlang conf file
		#smfile = conf_smfile.smfile(filepath)

		pass
