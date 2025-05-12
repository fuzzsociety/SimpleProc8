; Simple MMIO test for SimpleProc-8
; MMIO registers at 0xF0-0xFF
; 0xF0: UART Status
; 0xF1: UART Control
; 0xF2-0xF5: Circular buffer (4 bytes)
; 0xF6: Head pointer
; 0xF7: Tail pointer
; 0xF8: TX Data
; 0xF9: RX Data

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
    
    ; Now read back the 4 bytes
    LD A, [0xF9]     ; Read first byte from RX register
    ST A, [0x80]     ; Store to memory for verification
    
    LD A, [0xF9]     ; Read second byte
    ST A, [0x81]     ; Store to memory
    
    LD A, [0xF9]     ; Read third byte
    ST A, [0x82]     ; Store to memory
    
    LD A, [0xF9]     ; Read fourth byte
    ST A, [0x83]     ; Store to memory
    
    ; Send a byte via TX
    LD A, #0x58      ; 'X'
    ST A, [0xF8]     ; Send via TX register
    
    ; Check status register (should have bits set)
    LD A, [0xF0]     ; Read status register
    ST A, [0x84]     ; Store for verification
    
    HLT              ; End program
