; Test 5: Carry Flag and JC
; Result stored at [0x8C]
; Expected: 0x01

    LD A, #0xFF       ; Load 0xFF into register A
    LD B, #0x01       ; Load 0x01 into register B
    ADD A, B          ; A = A + B (0xFF + 0x01 = 0x00 with carry)
    
    JC carry_set      ; Jump if carry flag is set
    
    ; This code should be skipped
    LD A, #0xFF       
    ST A, [0x8C]
    JMP end_test_5
    
carry_set:
    LD A, #0x01       ; A = 1 indicating success
    ST A, [0x8C]      ; Store result
    
end_test_5:
    HLT               ; Halt execution
