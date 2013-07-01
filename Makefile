#this makefile is used for assembling, testing and generating [SFT]make parts.
PARTSDIR=parts
TESTSDIR=tests
TARGETFILE=sftmake

all: tests todo

#target for running all tests
tests: assembly testpartsq autoparsertestq testassemblyq runtests

$(TARGETFILE): parser
	@#first, copy the header
	@echo "Assembling $(TARGETFILE)"
	@echo "Adding header.py"
	@cp header.py "$(TARGETFILE)"
	@#add every file that has a symlink in $PARTSDIR
	@for FILE in $(PARTSDIR)/*; do PART=$$(basename "parts/$$(readlink "$$FILE")"); echo -e "\n\n\n# BEGIN FILE $$PART\n\n\n" >> $(TARGETFILE) && cat $$PART >> $(TARGETFILE) && echo "Adding $$PART"; done
	@#add final lines
	@echo -e "\n\n\n# End of assembled [SFT]make file" >> $(TARGETFILE)
	@echo -e "# Assembled at $(date)" >> $(TARGETFILE)

autoparser.py: grammar.wi
	@#invoke the wisent parser generator
	@#note that a modified python3 version of wisent is required, which generates valid python3 code.
	@#for the list of patches, see the python3-wisent package in the arch user repository:
	@#https://aur.archlinux.org/packages/python3-wisent/
	wisent -o autoparser.py -e autoparsertest.py grammar.wi
	@chmod +x autoparser.py

#PHONY targets for faster invocation
assembly: $(TARGETFILE)
parser: autoparser.py

#targets for running tests
testparts:
	@for FILE in $(PARTSDIR)/*; do PART=$$(basename "parts/$$(readlink "$$FILE")"); echo ./$$PART; python3 $$PART || exit 1; done

#this is the quiet version of testparts
testpartsq:
	@for FILE in $(PARTSDIR)/*; do PART=$$(basename "parts/$$(readlink "$$FILE")"); echo ./$$PART '1>/dev/null'; python3 $$PART 1>/dev/null || exit 1; done

autoparsertest: parser
	./autoparsertest.py

#this is the quiet version of autoparsertest
autoparsertestq: parser
	./autoparsertest.py 1>/dev/null

testassembly: assembly
	./$(TARGETFILE)

#this is the quiet version of testassembly
testassemblyq: assembly
	./$(TARGETFILE) 1>/dev/null

#targets for running tests
runtests:
	@for FILE in $(TESTSDIR)/*; do PART=$$(basename "parts/$$(readlink "$$FILE")"); echo ./$$PART; python3 $$PART || exit 1; done
	@echo -e "\x1b[32mAll good\x1b[m"

todo:
	@#search for all TODO entries in python files
	@find . -type f -regex '.*\.py' -exec sh -c 'RESULTS="$$(grep -n -B3 -A3 --color=always TODO {})"; test -n "$$RESULTS" && echo -e "\x1b[33m{}\x1b[m" && echo "$$RESULTS"' \;

clean:
	rm -r __pycache__

.PHONY: assembly parser testparts testpartsq autoparsertest autoparsertestq testassembly testassemblyq runtests tests todo clean
