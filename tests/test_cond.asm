; Test 4: Conditional Branching
; Results stored at [0x89], [0x8A], [0x8B]
; Expected: 0x01, 0x01, 0x01
;
; NOTE: LD does not affect flags on SimpleProc-8. Each conditional branch is
; preceded by an INC/DEC that sets the Zero flag, matching the idiom used by
; the loop and factorial tests.

    ; Test JMP (unconditional)
    LD A, #0x00       ; Initialize A to 0
    JMP unconditional_jump

    ; This code should be skipped
    LD A, #0xFF       ; If executed, this would set A to 0xFF
    JMP test_failed

unconditional_jump:
    LD A, #0x01       ; A = 1 indicating success
    ST A, [0x89]      ; Store result

    ; Test JZ (should jump when the Zero flag is set)
    LD A, #0x01       ; A = 1
    DEC A             ; A = 0  -> sets Z = 1
    JZ zero_jump      ; Should jump because the result is zero

    ; This code should be skipped
    LD A, #0xFF
    JMP test_failed

zero_jump:
    LD A, #0x01       ; A = 1 indicating success
    ST A, [0x8A]      ; Store result

    ; Test JNZ (should jump when the Zero flag is clear)
    LD A, #0x00       ; A = 0
    INC A             ; A = 1  -> sets Z = 0
    JNZ nonzero_jump  ; Should jump because the result is non-zero

    ; This code should be skipped
    LD A, #0xFF
    JMP test_failed

nonzero_jump:
    LD A, #0x01       ; A = 1 indicating success
    ST A, [0x8B]      ; Store result

    JMP end_test_4

test_failed:
    LD A, #0x00       ; A = 0 indicating failure
    ST A, [0x89]      ; Store result for JMP
    ST A, [0x8A]      ; Store result for JZ
    ST A, [0x8B]      ; Store result for JNZ

end_test_4:
    HLT               ; Halt execution
