main:
LD A, #2
ADD A, C
DEC A
JZ hang
JMP test_ZF

hang:
LD A, #0xFF
HLT

test_ZF:
LD A, #11
HLT