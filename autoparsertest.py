#! /usr/bin/env python
# autoparsertest.py - illustrate the use of a Wisent-generated parser
# example code autogenerated on 2013-03-09 18:45:00
# generator: wisent 0.6.2, http://seehuhn.de/pages/wisent
# source: assignmentgrammar.wi

from sys import stderr

from autoparser import Parser

def print_tree(tree, terminals, indent=0):
    """Print a parse tree to stdout."""
    prefix = "    "*indent
    if tree[0] in terminals:
        print(prefix + repr(tree))
    else:
        print(prefix + str(tree[0]))
        for x in tree[1:]:
            print_tree(x, terminals, indent+1)

input = [ ('IDENTIFIER',), (',',), ('IDENTIFIER',), ('=',), (',',),
          ('IDENTIFIER',), ('WHITESPACE',), ('[',), ('(',), ('IDENTIFIER',),
          ('=',), ('IDENTIFIER',), (',',), ('IDENTIFIER',), ('=',),
          ('IDENTIFIER',), (';',), ('IDENTIFIER',), ('=',), ('IDENTIFIER',),
          (',',), ('IDENTIFIER',), ('=',), ('IDENTIFIER',), (')',), ('&',),
          ('!',), ('IDENTIFIER',), ('=',), ('IDENTIFIER',), (',',),
          ('IDENTIFIER',), ('=',), ('IDENTIFIER',), (';',), ('IDENTIFIER',),
          ('=',), ('IDENTIFIER',), (',',), ('IDENTIFIER',), ('=',),
          ('IDENTIFIER',), (';',), ('IDENTIFIER',), ('=',), ('IDENTIFIER',),
          (',',), ('IDENTIFIER',), ('=',), ('IDENTIFIER',), (']',), (':',),
          ('=',), ('IDENTIFIER',), ('WHITESPACE',), ("'",), ('WHITESPACE',),
          ("'",), ('$',), ('(',), ('IDENTIFIER',), (')',) ]

p = Parser()
try:
    tree = p.parse(input)
except p.ParseErrors as e:
    for token,expected in e.errors:
        if token[0] == p.EOF:
            print >>stderr, "unexpected end of file"
            continue

        found = repr(token[0])
        if len(expected) == 1:
            msg = "missing %s (found %s)"%(repr(expected[0]), found)
        else:
            msg1 = "parse error before %s, "%found
            l = sorted([ repr(s) for s in expected ])
            msg2 = "expected one of "+", ".join(l)
            msg = msg1+msg2
        print >>stderr, msg
    raise SystemExit(1)

print_tree(tree, p.terminals)
