#!/usr/bin/python3
from parser.tokenizer import tokenize_statement
from logger.levels import *

statements = [
	"c:=gcc",
	"cflags[($mode==dbg)or (   $c in[clang  clang++ ])]+=-g -O0"
]

def run():
	for statement in statements:
		message("statement: " + statement)
		message(list(tokenize_statement(statement)))
