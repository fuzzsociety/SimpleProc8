; Test 10: Factorial Calculation for n=5
; Results stored at [0x99]
; Expected: 0x78 (120 decimal)

    LD A, #0x06       ; Initialize n to 5
    LD B, #0x01       ; Initialize result to 1
    
factorial_loop:
    ST A, [0x90]      ; Save current n to memory
    LD C, A           ; C = current value of n to use as counter
    LD D, #0x00       ; D = product accumulator (starts at 0)
    
multiply_loop:
    ADD D, B          ; Add current factorial value to product
    DEC C             ; Decrement counter
    JZ multiply_done  ; If counter reaches zero, multiplication is done
    JMP multiply_loop ; Otherwise continue multiplying
    
multiply_done:
    LD B, D           ; Move product back to B (our running result)
    LD A, [0x90]      ; Restore current n from memory
    DEC A             ; Decrement n for next factorial step
    JZ factorial_done ; If n=0, we're done
    JMP factorial_loop ; Otherwise continue factorial loop
    
factorial_done:
    ST B, [0x99]      ; Store final result
    HLT               ; Halt execution
