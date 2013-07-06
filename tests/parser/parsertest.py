#!/usr/bin/python3
from parser.parser import parse_statement, wisent_parsetree_to_string
from logger.levels import *

statements = [
	"c:=gcc",
	"cflags[($mode==dbg)or (   $c in[clang  clang++ ])]+=-g -O0",
	"asdf-=[a b [c d]]"
]

def run():
	for statement in statements:
		message("statement: " + statement)
		wisent_parsetree = parse_statement(statement)
		message(wisent_parsetree_to_string(wisent_parsetree))
