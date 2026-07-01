; Test: pointer-style indirection through a pointer held in memory.
;
; The ISA has no single-instruction memory-indirect mode ("[0x65]" is just
; direct addressing). True pointer indirection is done in two steps: load the
; pointer from memory into register B, then dereference B with [B].
;
;   1. mem[0x44] = 5          (the value we ultimately want)
;   2. mem[0x65] = 0x44       (a pointer stored in memory)
;   3. B = mem[0x65] = 0x44   (load the pointer into B)
;   4. D = mem[B] = mem[0x44] = 5   (dereference the pointer)
;
; Expected result: D = 5  (NOT 0x44, the pointer value)

    LD A, #5          ; A = 5
    ST A, 0x44        ; mem[0x44] = 5              (the target value)

    LD B, #0x44       ; B = 0x44                   (the address, as a constant)
    ST B, 0x65        ; mem[0x65] = 0x44           (store the pointer in memory)

    LD B, 0x65        ; B = mem[0x65] = 0x44       (load pointer back into B)
    LD D, [B]         ; D = mem[B] = mem[0x44] = 5 (dereference -> D = 5)

    HLT               ; Halt execution
