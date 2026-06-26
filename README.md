# SimpleProc8
This repository from fuzzsociety.org contains a basic CPU written in Python3 - The SimpleProc8 (This should sound in Italian as simple prosciutto - ham)

This is the original repository OpenSecurityTraining2 Architecture 1901 From Zero to QEMU course.

https://ost2.fyi/Arch1901

## Testing 

You have a basic test suite with jumps, conditions, even bubblesort.

Run `./run_tests.sh` from the repository root to assemble every `tests/*.asm`
from scratch (into a throwaway build directory) and execute each program. It
prints a table of ✓/✗ for assembly and execution along with the number of
instructions executed, and exits non-zero if any test fails. A test passes only
if it assembles cleanly and the program halts via `HLT` without crashing or
exceeding the interpreter's instruction cap.


## Collaboration

Send your PRs - we will look at them

## CPU Structure
Check the README_interpreter.md


## 2-pass Assembler Structure
This is very rudimentary still it will work to build pretty complex programs the README_asm.md contains the details


## Binary Ninja Plugin
I also prepared a binary ninja disassembler plugin - That is useful to understand how architectures are coded into such powerful tools

~/Library/Application\ Support/Binary\ Ninja/plugins/simpleproc8

should contain - README.md    __init__.py  plugin.json
