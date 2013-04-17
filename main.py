#!/usr/bin/python3

# this file is part of [sft]make
#
# licensed GPLv3 or later, no warranty, gschichten.
#
# main sftmake entry file, currently using conf-pysmfile
# for configuration
#
# (c) 2013 [sft]technologies, jonas jelten

import sys
import util
import re

import conf_pysmfile

#import argparse


def open_smfile(filepath):

	with open(filepath) as f:
		firstline = f.readline()

	#if the first line of the smfile contains "python",
	#it is written in python.
	if re.match(r"#.*python.*", firstline):
		#python conf file
		smfile = conf_pysmfile.pysmfile(filepath)
		pass

	#elif: #TODO: smlang smfile

	else:
		raise Exception("unknown config file header")
		#smlang conf file
		#smfile = conf_smfile.smfile(filepath)

		pass

def main():
	print("gschichten ausm paulanergarten")

	args = sys.argv

	print("number of args:" + str(len(args)))
	print(str(args))

	smroot = util.get_smroot()

	#TODO: may have other names
	root_smfile = smroot + "/smfile"


	smfile = open_smfile(root_smfile)
	smfile = conf_pysmfile.pysmfile(root_smfile)
	smfile_content = smfile.get_content()

	print("################ content of smfile:")
	print(smfile_content)

	print("################ end of smfile content\n\n")

	smfile.run()

if __name__ == "__main__":
	main()
