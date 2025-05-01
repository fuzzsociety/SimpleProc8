;Initialize registers
LD A, #0      ; Initialize sum to 0
LD B, #1      ; Initialize counter to 1
LD C, #4      ; Set limit to 100
LOOP:
    ADD A, B      ; Add current number to sum
    INC B         ; Increment counter
    LD D, C       ; Copy limit to D
    SUB D, B      ; D = D - B (D = C+1 - B)
    JZ END        ; If B == C+1, exit loop (zero result means equal)
    JNZ LOOP      ; If B < C+1, continue loop
END:
    ST A, [0x80]  ; Store result at memory location 0x80
    HLT           ; Halt the processor
