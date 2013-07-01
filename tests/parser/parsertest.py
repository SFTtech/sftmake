#!/usr/bin/python3
from parser.parser import parse_statement
from logger.levels import *

statements = [
	"c:=gcc",
	"cflags[($mode==dbg)or (   $c in[clang  clang++ ])]+=-g -O0"
]

def run():
	for statement in statements:
		message("statement: " + statement)
		message(parse_statement(statement))
