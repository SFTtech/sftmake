#!/usr/bin/python3
from tokenizer import tokenize_statement

statements = [
	"c:=gcc",
	"cflags[($mode==dbg)or (   $c in[clang  clang++ ])]+=-g -O0"
]

def run():
	for statement in statements:
		print("statement: " + statement)
		print(list(tokenize_statement(statement)))
