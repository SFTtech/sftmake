from logger import LogLevel

#a few example log levels
#ofc, nobody prevents you from defining your own, but your life will be a lot easier if you just do
#from logger.levels import *
fatal =     LogLevel(50, "FAT", "1;31")
error =     LogLevel(40, "ERR", "31")
warning =   LogLevel(30, "WRN", "33")
important = LogLevel(20, "IMP", "37")
message =   LogLevel(10, "MSG", "")
debug =     LogLevel(00, "DBG", "")
