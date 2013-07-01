#!/usr/bin/python3

# this file is part of [sft]make
#
# licensed GPLv3 or later, no warranty, gschichten.
#
# main sftmake entry file, currently using conf-pysmfile
# for configuration
#
# (c) 2013 [sft]technologies, jonas jelten



#TODO: gnu make compatibility (configure, make, make install) (incl. options)

#TODO: add testing features and bisect support




import sys
import os.path
import util
import re
from pprint import pprint
import dirscanner

import conf_smfile

#import argparse



def main():
	print("gschichten ausm paulanergarten")

	args = sys.argv

	print("number of args:" + str(len(args)))
	print(str(args))


	#default sftmake config
	sftmake_path = os.path.dirname(os.path.realpath(__file__))
	defaultconf = conf_smfile.smfile_factory(sftmake_path +"/conf_default.py")
	defaultconf.run()
	print("default configuration:")
	print(defaultconf.data)


	smroot = util.get_smroot()
	#filetree = dirscanner.smtree(util.relpath(smroot))
	filetree = dirscanner.smtree(util.relpath(smroot))

	print(str(filetree))

	root_smfile_name = filetree.get_root_smfile()

	#create a smfile handle, may be python or smlang
	root_smfile = conf_smfile.smfile_factory(root_smfile_name)

	#read the root smfile
	root_smfile.run()
	#TODO: add config in root smfile which specifies the directories
	#      to be scanned.

	mainfileconf = root_smfile.data
	print("project main configuration:")
	print(mainfileconf)


if __name__ == "__main__":
	main()
