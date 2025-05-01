; Test case to reproduce the factorial jump issue
; This should create the same jump offset problems

    LD A, #4          ; Initialize outer counter
    LD B, #1          ; Initialize result

outer_loop:
    ST A, [0x90]      ; Save outer counter
    LD C, A           ; Initialize inner counter
    LD D, #0          ; Initialize inner accumulator
    
inner_loop:
    ADD D, B          ; Add B to accumulator
    DEC C             ; Decrement inner counter
    JZ inner_done     ; If counter is zero, exit inner loop
    JMP inner_loop    ; Otherwise continue inner loop
    
inner_done:
    LD B, D           ; Save result from inner loop
    LD A, [0x90]      ; Restore outer counter
    DEC A             ; Decrement outer counter
    JZ outer_done     ; If outer counter is zero, we're done
    JMP outer_loop    ; Otherwise continue outer loop
    
outer_done:
    ST B, [0x99]      ; Store final result
    HLT               ; Halt
