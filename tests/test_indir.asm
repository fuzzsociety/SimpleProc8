; Test 7: Indirect Addressing
; Result stored at [0x8F]
; Expected: 0x42

    LD A, #0x90       ; Load address 0x90 into register A
    LD B, #0x42       ; Load value 0x42 into register B
    ST B, [0x90]      ; Store 0x42 at address 0x90
    
    LD C, [A]         ; Indirect load: C = content at address stored in A
    ST C, [0x8F]      ; Store result
    
    HLT               ; Halt execution
