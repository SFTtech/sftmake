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
import dirscanner

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

	if isinstance(filepath, dirscanner.sftmake_file):
		filepath = filepath.fullname

	if filepath.endswith(r".py"):
		#python conf file

		from conf_pysmfile import pysmfile
		smfile = pysmfile(filepath)
		return smfile

	#TODO: smlang smfile
	else:
		print("here the smlang-smfile would be created")
	#	smlang conf file
	#	from conf_smsmfile import smsmfile
	#	smfile = smsmfile(filepath)
	#	return smfile
