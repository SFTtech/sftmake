import os
import re

from logger.levels import *

#must be set externally, by calling util.set_smroot(path)
smroot = None


def abspath(path, relto = '^'):
	"""
	if path is absolute, don't change it
	if path is smpath, convert it to absolute
	if path is rel, convert it to absolute
	"""

	#if the path is empty, fak u
	if not path:
		raise Exception('Path must not be empty')

	smroot = get_smroot()

	#if the path starts with '/', it's already absolute
	if path[0] == '/':
		#debug("already abspath")
		result = path

	#if the path starts with '^', we need to replace that with smroot
	elif path[0] == '^':
		#debug("replacing ^ with real smroot")
		result = smroot + '/' + path[1:]

	#else, the path is relative... to relto
	else:
		#debug("making path absolute to relto")
		#debug("- path: " + path)
		#debug("- relto: " + relto)
		if relto[0] != '^':
			raise Exception('relto must start with ^')

		abs_relto = abspath(relto)
		#debug("=> making " + relto + " absolute = " + abs_relto)
		result = abs_relto + "/" + os.path.relpath(path, abs_relto)

	#debug("- result: " + result)
	return os.path.normpath(result)

def relpath(path, relto = '^'):
	"""
	if path is absolute, convert it to rel
	if path is smpath, convert it to rel
	if path is rel, don't change it
	"""

	if not path: #fak u
		raise Exception("Path must not be empty")

	if path[0] == '/':
		result = os.path.relpath(path, abspath(relto))

	elif path[0] == '^':
		smroot = get_smroot()
		result = os.path.relpath(smroot + '/' + path[1:], abspath(relto))

	else:
		smroot = get_smroot()
		result = os.path.relpath(path, abspath(relto))

	return result

def smpath(path, relto = '^'):
	"""
	if path is absolute, convert it to smpath
	if path is smpath, don't change it
	if path is rel, convert it to smpath
	"""

	#if the path is empty, fak u
	if not path:
		raise Exception("Path must not be empty")

	smroot = get_smroot()

	#if the path starts with '^', it's an sftmake path that may need a relative conversion
	if path[0] == '^':
		path = smroot + '/' + path[1:]

	#else, get relative path
	if not path[0] == '/':
		path = abspath(path, relto)

	#generate path relative to smroot (to just add ^ then)
	path = os.path.relpath(path, smroot)

	if(path == '.'):
		return '^'
	else:
		return '^/' + path


def rppath(path):
	"""
	append the smroot to the given path
	"""

	if path[0] == '^':
		raise Exception("fak u, you already got a smpath as prefix...")

	return os.path.normpath(get_smroot() + "/" + path)


def smpathifrel(path, relto = '^'):
	"""
	if path is absolute, don't change it
	if path is smpath, don't change it
	if path is rel, change it to smpath
	"""
	#if the path is empty, fak u
	if not path:
		raise Exception("Path must not be empty")

	elif path[0] == '/':
		return path

	else:
		return smpath(path, relto)


#TODO Decide on an encoding. It can be made arbitrarily complicated.
def generate_oname(obj_desc):
	"""Encodes the object name/command description in order to be sanely
	and intuitively displayed as a filename.

	The colon is the escape character; escaping colons requires a double
	colon.
	"""
	# Escape any colons present in the string (why would you put colons in
	# a string? Seriously?)
	obj_desc = re.sub(r":", "::", obj_desc)
	# Escape underscores and pipe characters
	obj_desc = re.sub(r"\|", ":|", obj_desc)
	obj_desc = re.sub(r"_", ":_", obj_desc)
	# Finally, replace spaces with underscores and slashes with vertical pipes.
	# If your filename contains any other evil characters,
	# then God - er - Gnu help you.
	obj_desc = re.sub(r" ", "_", obj_desc)
	obj_desc = re.sub(r"/", "|", obj_desc)
	obj_desc = re.sub(r"=", "-", obj_desc)
	# And_there_you_go::_A_weirdly:/interestingly-escaped_command.
	return obj_desc

def get_smroot():
	global smroot

	if smroot == None:
		raise Exception("smroot must be set e.g. by dirscanner.smtree('./basedir/').get_root_smfile().directory")
	return smroot

def set_smroot(newroot):
	"""
	actually this is totally dirty and should be forbidden.
	"""
	global smroot

	smroot = newroot

def in_smdir(path):
	'''
	return true, if the path lies within the smroot dir or a subfolder
	return false, if the path is e.g. a system path in /usr/lib

	use this function to test if e.g. a header is a system header
	or belongs to the project itself.
	'''

	smroot = os.path.normpath(get_smroot())

	filepath = abspath(path)

	#prefix of smroot and filepath must be smroot
	#then the file lies within the sm project directory

	if os.path.commonprefix([smroot, filepath]).startswith(smroot):
		return True
	else:
		return False

	pass

def parent_folder(path):
	if path == "^":
		res = "project"
	else:
		res = os.path.dirname(path)
	return res
