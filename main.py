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

import conf_pysmfile

#import argparse

def main():
	print("gschichten ausm paulanergarten")

	args = sys.argv

	print("number of args:" + str(len(args)))
	print(str(args))

	smroot = util.get_smroot()

	#TODO: may have other names
	root_smfile = smroot + "/smfile"


	smfile = conf_pysmfile.pysmfile(root_smfile)
	smfile_content = smfile.dump_content()


if __name__ == "__main__":
	main()
