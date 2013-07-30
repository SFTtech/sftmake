import sm

#example configuration for a binary which links to a library, e.g. rary

sftmake = sm.smconfig()

sftmake.set('ldflags', ['-L ./ -l rary'])
sftmake.set('depends', ['^/library.so'])


sftmake.set('use', ['roflfolder/asdf.c', 'main.c'])
