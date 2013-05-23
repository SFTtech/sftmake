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

	def __init__(self, fname, smobj=None):
		self.filename = fname
		if smobj != None:
			self.smobj = smobj

		with open(self.filename) as f:
			self.content = f.read()

		self.data = None

	def get_content(self):
		return self.content

	def run(self):
		raise NotImplementedError("run method must be implemented")


def smfile_factory(fobj):

	if isinstance(fobj, dirscanner.simple_file):
		filename = fobj.fullname
	else:
		filename = fobj
		fobj = None

	#create smfile wrapper/handler accordung to it's file extension
	if filename.endswith(r".py"):
		#python conf file

		from conf_pysmfile import pysmfile
		smfile = pysmfile(filename, fobj)
		return smfile

	#TODO: smlang smfile
	else:
		raise Exception("only python smfiles supported yet.")
	#	smlang conf file
	#	from conf_smsmfile import smsmfile
	#	smfile = smsmfile(filepath)
	#	return smfile
