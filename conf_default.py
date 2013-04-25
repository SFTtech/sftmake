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

print("lol")

sftmake = smconfig()
sftmake.lol()

#TODO use environment variables!

sftmake.set('c', 'clang')
sftmake.set('cflags', '-g -O3')
