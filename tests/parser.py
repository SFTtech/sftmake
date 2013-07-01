#!/usr/bin/python3
from parser import parse_statement

statements = [
	"c:=gcc",
	"cflags[($mode==dbg)or (   $c in[clang  clang++ ])]+=-g -O0"
]

def run():
	for statement in statements:
		print("statement:")
		print(parse_statement(statement))
