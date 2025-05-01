; Test 3: Logical Operations
; Results stored at [0x85], [0x86], [0x87], [0x88]
; Expected: 0x01, 0x07, 0x06, 0xFA

    LD A, #0x05       ; Load 0x05 (0b0101) into register A
    LD B, #0x03       ; Load 0x03 (0b0011) into register B
    
    ; AND test
    AND A, B          ; A = A & B (0b0101 & 0b0011 = 0b0001 = 0x01)
    ST A, [0x85]      ; Store result
    
    ; OR test
    LD A, #0x05       ; Reset A to 0x05 (0b0101)
    OR A, B           ; A = A | B (0b0101 | 0b0011 = 0b0111 = 0x07)
    ST A, [0x86]      ; Store result
    
    ; XOR test
    LD A, #0x05       ; Reset A to 0x05 (0b0101)
    XOR A, B          ; A = A ^ B (0b0101 ^ 0b0011 = 0b0110 = 0x06)
    ST A, [0x87]      ; Store result
    
    ; NOT test
    LD A, #0x05       ; Reset A to 0x05 (0b0101)
    NOT A             ; A = ~A (invert all bits, ~0b0101 = 0b1111 1010 = 0xFA)
    ST A, [0x88]      ; Store result
    
    HLT               ; Halt execution
