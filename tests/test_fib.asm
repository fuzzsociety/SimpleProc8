; Test 9: Fibonacci Sequence (first 8 numbers)
; Results stored at [0x91] through [0x98]
; Expected: 0x01, 0x01, 0x02, 0x03, 0x05, 0x08, 0x0D, 0x15

    LD A, #0x01       ; Initialize first Fibonacci number
    LD B, #0x01       ; Initialize second Fibonacci number
    
    ; Store first two numbers
    ST A, [0x91]
    ST B, [0x92]
    
    ; Calculate and store next 6 Fibonacci numbers
    ADD C, A, B       ; C = A + B (fib3 = fib1 + fib2)
    ST C, [0x93]
    
    LD A, B           ; A = B (A becomes fib2)
    LD B, C           ; B = C (B becomes fib3)
    
    ADD C, A, B       ; C = A + B (fib4 = fib2 + fib3)
    ST C, [0x94]
    
    LD A, B           ; Shift values forward
    LD B, C
    
    ADD C, A, B       ; C = A + B (fib5)
    ST C, [0x95]
    
    LD A, B
    LD B, C
    
    ADD C, A, B       ; C = A + B (fib6)
    ST C, [0x96]
    
    LD A, B
    LD B, C
    
    ADD C, A, B       ; C = A + B (fib7)
    ST C, [0x97]
    
    LD A, B
    LD B, C
    
    ADD C, A, B       ; C = A + B (fib8)
    ST C, [0x98]
    
    HLT               ; Halt execution
