#!/usr/bin/python3
import os
import re




class EnumVal:
	def __init__(self, representation):
		self.representation = representation

	def __repr__(self):
		return repr(self.representation)

class OrderedSet:
	""" wrapper around OrderedDict because fak u python

	we just need OrderedSet functionality, so we set val = None for all keys. dirty, nah?"""
	def __init__(self):
		from collections import OrderedDict
		self.storage = OrderedDict()

	#append an element
	#returns true if the element was new
	def append(self, x):
		if(x in self.storage):
			self.storage.pop(x)
			self.storage[x] = None
			return False
		else:
			self.storage[x] = None
			return True

	#delete an element
	def delete(self, x):
		self.storage.pop(x)

	#remove all elements
	def clear(self):
		self.storage.clear()

	#update the ordered set with an other ordered set
	def update(self, x):
		for v in x:
			self.storage.pop(v)
		self.storage.update(x.storage)

	def tolist(self):
		return [x for x in self.storage]

	def newest(self):
		return next(reversed(self.storage))

	def __iter__(self):
		return self.storage.__iter__()


smroot = None #will be set once needed, see below

#functions for path conversions

#convert path to absolute POSIX path
def abspath(path, relto = '^'):
	global smroot

	#if the path is empty, fak u
	if(not path):
		raise Exception('Path must not be empty')

	if smroot == None:
		smroot = find_smroot()

	#if the path starts with '/', it's already absolute
	if(path[0] == '/'):
		result = path

	#if the path starts with '^', we need to replace that with smroot
	elif(path[0] == '^'):
		result = smroot + '/' + path[1:]

	#else, the path is relative... to relto
	else:
		if(relto[0] != '^'):
			raise Exception('relto must start with ^')
		result = abspath(relto) + '/' + path

	return os.path.normpath(result)

#convert path to relative POSIX path
def relpath(path, relto = '^'):
	global smroot

	if(not path): #fak u
		raise Exception("Path must not be empty")

	elif(path[0] == '/'):
		return os.path.relpath(path, abspath(relto))

	if smroot == None:
		smroot = find_smroot()

	if(path[0] == '^'):
		return os.path.relpath(smroot + '/' + path[1:], abspath(relto))

	#else, path is already relative to relto
	else:
		return os.path.normpath(path)

#convert path to sftmake path
def smpath(path, relto = '^'):
	global smroot

	#if the path is empty, fak u
	if(not path):
		raise Exception("Path must not be empty")

	#if the path starts with '^', it's already an sftmake path
	if(path[0] == '^'):
		return path

	if smroot == None:
		smroot = find_smroot()

	#else, get relative path
	if(path[0] != '/'):
		path = abspath(path, relto)

	#generate path relative to smroot (to just add ^ then)
	path = os.path.relpath(path, smroot)

	if(path == '.'):
		return '^'
	else:
		return '^/' + path

#convert path to sftmke path if it is relative
def smpathifrel(path, relto = '^'):
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
	# And_there_you_go::_A_weirdly:/interestingly-escaped_command.
	return obj_desc


def find_smroot():
	path = os.path.abspath('.')
	while(not os.path.isfile(path + "/smfile")):
		if(path == "/"):
			raise Exception("No smfile found")
		else:
			path = os.path.abspath(path + '/..')
	return path


def in_smdir(path, relto = "^"):
	'''
	return true, if the path lies within the smroot dir or a subfolder
	return false, if the path is e.g. a system path in /usr/lib

	use this function to test if e.g. a header is a system header
	or belongs to the project itself.
	'''
	global smroot

	if smroot == None:
		smroot = find_smroot()

	filepath = abspath(path)

	#prefix of smroot and filepath must be smroot
	#then the file lies within the sm project directory

	if os.path.commonprefix([smroot, filepath]).startswith(smroot):
		return True
	else:
		return False

	pass
