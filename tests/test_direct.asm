; Test: bare (unbracketed) direct addressing for LD and ST
; Verifies that "LD Rx, addr" / "ST Rx, addr" (no brackets) assemble and
; execute identically to the bracketed "[addr]" form, for both numeric
; addresses and labels.
;
; Expected results:
;   C        = 0x37   (bare numeric load)
;   D        = 0xAB   (bare label load)
;   [0x90]   = 0x37   (bare numeric store)
;   [0x91]   = 0x37   (bracketed store, for comparison)
;   [datum]  = 0xAB   (bare label store)

    LD A, #0x37      ; A = 0x37
    ST A, 0x90       ; bare numeric store   -> mem[0x90] = 0x37
    LD C, 0x90       ; bare numeric load    -> C = 0x37
    ST C, [0x91]     ; bracketed store      -> mem[0x91] = 0x37 (same encoding)

    LD A, #0xAB      ; A = 0xAB
    ST A, datum      ; bare label store     -> mem[datum] = 0xAB
    LD D, datum      ; bare label load      -> D = 0xAB
    HLT

datum:
    NOP              ; data byte written by the stores above
