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

	def __init__(self, fileobj):
		self.fileobj = fileobj
		self.data = None

		with open(self.fileobj.fullname) as f:
			self.content = f.read()

	def get_content(self):
		"""return the real smfile content"""
		return self.content

	def run(self):
		raise NotImplementedError("run method must be implemented")

	def get_associated_smname(self):
		return self.fileobj.get_associated_smname()


def smfile_factory(fobj):

	if not isinstance(fobj, dirscanner.simple_file):
		raise Exception("smfile creation needs to have a dirscanner.simple_file as argument")

	#create smfile wrapper/handler accordung to it's file extension
	if fobj.fullname.endswith(r".py"):
		#python conf file

		from conf_pysmfile import pysmfile
		smfile = pysmfile(fobj)
		return smfile

	#TODO: smlang smfile
	else:
		raise Exception("only python smfiles supported yet.")
	#	smlang conf file
	#	from conf_smsmfile import smsmfile
	#	smfile = smsmfile(filepath)
	#	return smfile
