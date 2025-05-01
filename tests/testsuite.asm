; Initialize registers
LD A, #0     ; A = 0
LD B, #1     ; B = 1
LD C, #127   ; C = 127 (max positive 8-bit signed)
LD D, #255   ; D = 255 (or -1 in signed)

; Test subtraction to set N and C flags
SUB A, A     ; A = 255 (-1), sets N and C flags
ST A, [0x80] ; Store A to memory

; Test addition to set Z and C flags
ADD A, D     ; A = 254, clears Z flag, sets C flag
ST A, [0x81] ; Store A to memory


; Test overflow with addition
LD A, C      ; A = 127
ADD A, B     ; A = 128, sets V and N flags
ST A, [0x82] ; Store A to memory

; Test logical operations
LD A, #0xAA  ; A = 10101010
LD B, #0x55  ; B = 01010101
AND A, B     ; A = 0, sets Z flag
ST A, [0x83] ; Store A to memory

OR A, B      ; A = 01010101, clears Z flag
ST A, [0x84] ; Store A to memory

XOR A, D     ; A = 10101010, clears Z flag
ST A, [0x85] ; Store A to memory

NOT A        ; A = 01010101
ST A, [0x86] ; Store A to memory

; Test jumps
LD A, #0     ; A = 0, sets Z flag
JZ 0x30      ; Jump if zero
NOP          ; Should be skipped
NOP          ; Should be skipped

; Address 0x30:
LD A, #42    ; A = 42
ST A, [0x87] ; Store A to memory
HLT          ; Halt execution
