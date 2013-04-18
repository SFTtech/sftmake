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

import conf_smfile

#import argparse



def main():
	print("gschichten ausm paulanergarten")

	args = sys.argv

	print("number of args:" + str(len(args)))
	print(str(args))

	smroot = util.get_smroot()

	#TODO: may have other names
	root_smfile = smroot + "/smfile"


	smfile = conf_smfile.smfile_factory(root_smfile)
	smfile_content = smfile.get_content()

	print("################ content of smfile:")
	print(smfile_content)

	print("################ end of smfile content\n\n")

	smfile.run()

if __name__ == "__main__":
	main()
