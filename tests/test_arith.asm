; Test 2: Arithmetic Operations
; Results stored at [0x81], [0x82], [0x83], [0x84]
; Expected: 0x07, 0x03, 0x05, 0x04

    LD A, #0x05       ; Load 5 into register A
    LD B, #0x02       ; Load 2 into register B
    
    ; Addition test
    ADD A, B          ; A = A + B (5 + 2 = 7)
    ST A, [0x81]      ; Store result
    
    ; Subtraction test
    LD A, #0x05       ; Reset A to 5
    SUB A, B          ; A = A - B (5 - 2 = 3)
    ST A, [0x82]      ; Store result
    
    ; Increment test
    INC A             ; A = A + 1 (3 + 1 = 4)
    INC A             ; A = A + 1 (4 + 1 = 5)
    ST A, [0x83]      ; Store result
    
    ; Decrement test
    DEC A             ; A = A - 1 (5 - 1 = 4)
    ST A, [0x84]      ; Store result
    
    HLT               ; Halt execution
