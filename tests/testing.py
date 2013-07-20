#!/usr/bin/python3
#quick functions for printing colored text easily
#call with no argument to get 'reset' colcode
def colcode(col=""):
	return "\x1b[" + str(col) + "m"

def coltext(text, col):
	return colcode(col) + text + colcode()

def colprint(text, col):
	print(coltext(text, col))

def redprint(text):
	colprint(text, "1;31")

def greenprint(text):
	colprint(text, 32)

def cyanprint(text):
	colprint(text, 36)

def testseries(name, testfun, testtostr, *tests):
	success = 0
	count = len(tests)
	countstr = str(count)
	countstrlen = len(countstr)

	for i, test in enumerate(tests):
		print(name + ": " + str(i).zfill(countstrlen) + "/" + countstr + ": " + testtostr(test))
		if(testfun(test)):
			success += 1

	message = name + ": " + str(success).zfill(countstrlen) + "/" + countstr + " successfull"
	if success == count:
		greenprint(message)
		return True
	else:
		redprint(message)
		return False
