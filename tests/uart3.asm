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
    
    ; Send 4 bytes via TX
    LD A, #0x41      ; 'A'
    ST A, [0xF8]     ; Send via TX register
    
    LD A, #0x42      ; 'B'
    ST A, [0xF8]     ; Send via TX register
    
    LD A, #0x43      ; 'C'
    ST A, [0xF8]     ; Send via TX register
    
    LD A, #0x44      ; 'D'
    ST A, [0xF8]     ; Send via TX register
    
    ; Zero out MMIO space
    LD A, #0x00      ; Zero value
    ST A, [0xF0]     ; Clear Status register
    ST A, [0xF1]     ; Clear Control register
    ST A, [0xF2]     ; Clear buffer[0]
    ST A, [0xF3]     ; Clear buffer[1]
    ST A, [0xF4]     ; Clear buffer[2]
    ST A, [0xF5]     ; Clear buffer[3]
    ST A, [0xF6]     ; Clear Head pointer
    ST A, [0xF7]     ; Clear Tail pointer
    ST A, [0xF8]     ; Clear TX register
    ST A, [0xF9]     ; Clear RX register
    
    ; Now read from RX until no more data available
    ; First read
    LD A, [0xF0]     ; Check status register
    ST A, [0x90]     ; Store status for verification
    LD A, [0xF9]     ; Read from RX register
    ST A, [0x80]     ; Store to memory for verification
    
    ; Second read
    LD A, [0xF0]     ; Check status register
    ST A, [0x91]     ; Store status for verification
    LD A, [0xF9]     ; Read from RX register
    ST A, [0x81]     ; Store to memory
    
    ; Third read
    LD A, [0xF0]     ; Check status register
    ST A, [0x92]     ; Store status for verification
    LD A, [0xF9]     ; Read from RX register
    ST A, [0x82]     ; Store to memory
    
    ; Fourth read
    LD A, [0xF0]     ; Check status register
    ST A, [0x93]     ; Store status for verification
    LD A, [0xF9]     ; Read from RX register
    ST A, [0x83]     ; Store to memory
    
    ; Fifth read (should have no data available)
    LD A, [0xF0]     ; Check status register
    ST A, [0x94]     ; Store status for verification
    LD A, [0xF9]     ; Read from RX register (may return old data or 0)
    ST A, [0x84]     ; Store to memory
    
    ; Store a marker to indicate test is complete
    LD A, #0xFF
    ST A, [0x8F]     ; Store marker at address 0x8F
    
    HLT              ; End program
