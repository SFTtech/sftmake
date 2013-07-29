import os
import re

from logger.levels import *

#must be set externally, by calling util.set_smroot(path)
smroot = None


def relpath(path, relto = "^"):
	#debug("making relpath of '" + path + "' relative to '" + relto + "'")
	if relto[0] == '^':
		relto = get_smroot() + relto[1:]
	if path[0] != '^':
		return path
	res = os.path.relpath(path[2:],relto)
	#debug("result = " + res)
	return res


def smpath(path, relto = "^"):
	#debug("making smpath of '" + path + "' relative to '" + relto + "'")
	if path[0] in '^': #TODO: maybe '^/'
		return path
	if relto[0] == '^':
		relto = get_smroot() + relto[1:]

	res = '^/' + os.path.relpath(path, relto)
	#debug("result = " + res)
	return res

def abspath(path, relto = "^"):
	return relpath(path, relto)


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
