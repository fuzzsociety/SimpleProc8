; Modified code to read only one byte after writing 4 bytes
    
    ; Initialize UART registers
    LD A, #0x80      ; Global interrupt enable
    ST A, [0xF1]     ; Store to interrupt control register
    
    ; Write 4 test bytes to circular buffer
    LD A, #0x41      ; 'A'
    ST A, [0xF2]     ; Store to buffer[0]
    
    LD A, #0x42      ; 'B'
    ST A, [0xF3]     ; Store to buffer[1]
    
    LD A, #0x43      ; 'C'
    ST A, [0xF4]     ; Store to buffer[2]
    
    LD A, #0x44      ; 'D'
    ST A, [0xF5]     ; Store to buffer[3]
    
    ; Set head and tail pointers
    LD A, #0x04      ; Head = 4 (full buffer)
    ST A, [0xF6]     ; Store head pointer
    
    LD A, #0x00      ; Tail = 0 (start reading from beginning)
    ST A, [0xF7]     ; Store tail pointer
    
    ; Now read only a single byte
    LD A, [0xF9]     ; Read one byte from RX register
    ST A, [0x80]     ; Store to memory for verification
    
    ; Send a byte via TX
    LD A, #0x58      ; 'X'
    ST A, [0xF8]     ; Send via TX register
    
    ; Check status register (should have bits set)
    LD A, [0xF0]     ; Read status register
    ST A, [0x84]     ; Store for verification
    
    HLT              ; End program