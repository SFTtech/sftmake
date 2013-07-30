import sm

#simple example configuration for creating the rary library (got it?).

sftmake = sm.smconfig()

sftmake.set('use', ['roflfolder/file.c', 'roflfolder/lmaodirectory/asdf.c', '^/library_main.c'])

sftmake.set('cflags', ['-fPIC'])
sftmake.set('ldflags', ['-shared -Wl,-soname,library.so'])

