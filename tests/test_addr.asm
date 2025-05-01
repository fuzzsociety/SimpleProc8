; Test 8: Register to Register Transfer
; Result stored at [0x90]
; Expected: 0x37

    LD A, #0x37       ; Load 0x37 into register A
    LD B, A           ; Copy value from register A to register B
    ST B, [0x90]      ; Store B to verify the transfer worked
    
    HLT               ; Halt execution
