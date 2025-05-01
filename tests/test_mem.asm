; Test 1: Memory Operations
; Result stored at [0x80]
; Expected: 0x42

    LD A, #0x42       ; Load immediate value 0x42 into register A
    ST A, [0x80]      ; Store register A value at memory location 0x80
    LD B, [0x80]      ; Load the value from memory location 0x80 into register B
    
    ; Test passes if we can successfully write and read memory
    ; (verified by inspection of memory at 0x80)
    
    HLT               ; Halt execution
