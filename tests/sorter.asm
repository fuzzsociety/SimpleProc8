; Bubble Sort implementation for SimpleProc-8
; Memory layout:
; 0x80-0xBF: Array to be sorted (64 elements max)
; 0xFD: Temporary storage for element swap
; 0xFE: Array length
; 0xFF: Temporary storage for inner loop counter

    ; Initialize array with test data (in reverse order to demonstrate sorting)
    LD A, #0x08      ; Start with value 8
    LD B, #0x80      ; Initialize array address pointer
init_loop:
    ST A, [B]        ; Store value at array position
    INC B            ; Move to next array position
    DEC A            ; Decrement value (creating reverse order: 8,7,6,5,4,3,2,1)
    JZ init_done     ; If we've reached 0, we're done
    JMP init_loop    ; Otherwise, continue filling
    
init_done:
    ; Store array length
    LD A, #0x08      ; 8 elements in our test array
    ST A, [0xFE]     
    
    ; Begin bubble sort
    LD C, [0xFE]     ; Get array length for outer loop
    DEC C            ; Need (length-1) passes
    
outer_loop:
    ; Initialize index for inner loop
    LD B, #0x80      ; Start at first array element
    LD A, [0xFE]     ; Get array length for inner loop
    DEC A            ; Need (length-1) comparisons
    ST A, [0xFF]     ; Store inner loop counter in 0xFF
    
inner_loop:
    ; Compare adjacent elements
    LD A, [B]        ; A = array[j]
    
    ; Get array[j+1]
    INC B            ; B points to array[j+1]
    LD D, [B]        ; D = array[j+1]
    DEC B            ; B back to array[j]
    
    ; Compare: For ascending sort, swap if array[j] > array[j+1]
    ; Using subtraction: A - D will set carry if A < D
    SUB A, D         ; A = array[j] - array[j+1]
    JC no_swap       ; If carry set (A < D), no swap needed (already in ascending order)
    JZ no_swap       ; If zero (A = D), no swap needed
    
    ; We get here if A > D, meaning array[j] > array[j+1], so swap needed
    LD A, [B]        ; A = array[j]
    ST A, [0xFD]     ; Save array[j] temporarily
    INC B            ; B points to array[j+1]
    LD A, [B]        ; A = array[j+1]
    DEC B            ; B back to array[j]
    ST A, [B]        ; array[j] = array[j+1]
    INC B            ; B points to array[j+1]
    LD A, [0xFD]     ; A = original array[j]
    ST A, [B]        ; array[j+1] = original array[j]
    DEC B            ; B back to array[j]
    
no_swap:
    ; Move to next pair
    INC B            ; Move to next element
    LD A, [0xFF]     ; Get inner loop counter
    DEC A            ; Decrement inner loop counter
    ST A, [0xFF]     ; Save updated counter
    JZ inner_done    ; If we've compared all pairs, inner loop is done
    JMP inner_loop   ; Otherwise, continue inner loop
    
inner_done:
    ; Continue outer loop
    DEC C            ; Decrement outer loop counter
    JZ sort_done     ; If we've done all passes, we're done
    JMP outer_loop   ; Otherwise, do another pass
    
sort_done:
    ; Array is now sorted
    LD A, #0xFF      ; Success marker
    ST A, [0x7F]     ; Store at address before array
    HLT              ; End program