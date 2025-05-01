; Initialize registers
LD A, #0      ; Initialize sum to 0
LD B, #1      ; Initialize counter to 1
SUB A, B
ST A, [0x80] ; Store result at memory location 0x80
HLT        ; Halt the processor
