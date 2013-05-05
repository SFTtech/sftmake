#!/usr/bin/python3
# sftmake:pythonconfig

# this file is part of [sft]make
#
# licensed GPLv3 or later, no warranty, gschichten.
#
#
# sftmake default configuration file
#
# (c) 2013 [sft]technologies, jonas jelten



from sm import smconfig

sftmake = smconfig()
sftmake.lol()

#TODO use environment variables!

sftmake.set('c', 'gcc')
sftmake.set('cflags', '-march=native')

#sftmake.set('build', sm.everything)
