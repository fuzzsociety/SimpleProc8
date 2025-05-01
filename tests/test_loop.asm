; Test 6: Loop Implementation (Count from 10 down to 1)
; Results stored at [0x8D], [0x8E]
; Expected: 0x00, 0x0A (counter end value, iterations completed)

    LD A, #0x0A       ; Initialize counter to 10
    LD B, #0x00       ; Initialize iteration count to 0
    
loop_start:
    INC B             ; Increment iteration count
    DEC A             ; Decrement counter
    
    JZ loop_end       ; Exit loop when counter reaches 0
    JMP loop_start    ; Otherwise continue looping
    
loop_end:
    ST A, [0x8D]      ; Store final counter value (should be 0)
    ST B, [0x8E]      ; Store iteration count (should be 10)
    
    HLT               ; Halt execution
