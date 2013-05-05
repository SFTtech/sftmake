#!/usr/bin/python3
import os
import re

class EnumVal:
	"""
	simply functions as a named object, for use e.g. as enum value.
	"""
	def __init__(self, representation):
		self.representation = representation

	def __repr__(self):
		return repr(self.representation)

class OrderedSet:
	"""
	we emulate 'OrderedSet' functionality from an OrderedDict by setting
	val = None.
	fak u python for not providing OrderedSet.
	"""
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


#functions for path conversions

def abspath(path, relto = '^'):
	"""
	if path is absolute, don't change it
	if path is smpath, convert it to absolute
	if path is rel, convert it to absolute
	"""
	#if the path is empty, fak u
	if(not path):
		raise Exception('Path must not be empty')

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

def relpath(path, relto = '^'):
	"""
	if path is absolute, convert it to rel
	if path is smpath, convert it to rel
	if path is rel, don't change it
	"""
	if(not path): #fak u
		raise Exception("Path must not be empty")

	elif(path[0] == '/'):
		return os.path.relpath(path, abspath(relto))

	if(path[0] == '^'):
		return os.path.relpath(smroot + '/' + path[1:], abspath(relto))

	#else, path is already relative to relto
	else:
		return os.path.normpath(path)

def smpath(path, relto = '^'):
	"""
	if path is absolute, convert it to smpath
	if path is smpath, don't change it
	if path is rel, convert it to smpath
	"""
	#if the path is empty, fak u
	if(not path):
		raise Exception("Path must not be empty")

	#if the path starts with '^', it's already an sftmake path
	if(path[0] == '^'):
		return path

	#else, get relative path
	if(path[0] != '/'):
		path = abspath(path, relto)

	#generate path relative to smroot (to just add ^ then)
	path = os.path.relpath(path, smroot)

	if(path == '.'):
		return '^'
	else:
		return '^/' + path

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
	# And_there_you_go::_A_weirdly:/interestingly-escaped_command.
	return obj_desc

def concat(lists):
	for l in lists:
		for val in l:
			yield val
