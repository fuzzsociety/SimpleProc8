; Test 7: Indirect Addressing (B is the pointer register)
; Result stored at [0x8F]
; Expected: 0x42

    LD B, #0x90       ; B holds the address we want to dereference
    LD A, #0x42       ; value to place there
    ST A, [B]         ; mem[0x90] = 0x42  (indirect store via B)

    LD C, [B]         ; indirect load: C = content at address in B
    ST C, [0x8F]      ; store result
    LD A, 0x8F

    HLT               ; Halt execution
