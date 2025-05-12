; SimpleProc-8 UART Test Program
; MMIO registers at 0xF0-0xFF
; 0xF0: Status Register (bit 0: RX data available, bit 1: TX buffer empty, bit 7: IRQ pending)
; 0xF1: Control Register (bit 0: RX interrupt enable, bit 1: TX interrupt enable)
; 0xF2-0xF5: RX circular buffer (4 bytes)
; 0xF6: RX head pointer
; 0xF7: RX tail pointer
; 0xF8: TX data register (writing here sends a byte)
; 0xF9: RX data register (reading from here retrieves a byte)
; 0xE0: UART buffer print trigger

    ; Initialize UART
    LD A, #0x03      ; Enable both RX and TX interrupts
    ST A, [0xF1]     ; Store to control register
    
    ; Send four test bytes via TX
    LD A, #0x41      ; 'A'
    ST A, [0xF8]     ; Send via TX register
    
    LD A, #0x42      ; 'B'
    ST A, [0xF8]     ; Send via TX register
    
    LD A, #0x43      ; 'C'
    ST A, [0xF8]     ; Send via TX register
    
    LD A, #0x44      ; 'D'
    ST A, [0xF8]     ; Send via TX register
    
    ; Set RX buffer pointers
    LD A, #0x03      ; Head points to last written byte
    ST A, [0xF6]     ; Set RX head pointer
    
    LD A, #0x00      ; Start reading from beginning
    ST A, [0xF7]     ; Set RX tail pointer
    
    ; Set RX data available bit and IRQ pending
    LD A, #0x81      ; Set bit 0 (RX data available) and bit 7 (IRQ pending)
    ST A, [0xF0]     ; Update status register
    
    
    ; Read back the received data
    LD A, [0xF9]     ; Read first byte (from RX buffer[0])
    ST A, [0x80]     ; Store to memory location 0x80
    
    LD A, [0xF9]     ; Read second byte (from RX buffer[1])
    ST A, [0x81]     ; Store to memory location 0x81
    
    LD A, [0xF9]     ; Read third byte (from RX buffer[2])
    ST A, [0x82]     ; Store to memory location 0x82
    
    LD A, [0xF9]     ; Read third byte (from RX buffer[3])
    ST A, [0x83]     ; Store to memory location 0x83

    ; Check final status
    LD A, [0xF0]     ; Read status register
    ST A, [0x84]     ; Store to memory location 0x84
    
    ; Check final RX buffer pointers
    LD A, [0xF6]     ; Read RX head pointer
    ST A, [0x85]     ; Store to memory
    
    LD A, [0xF7]     ; Read RX tail pointer
    ST A, [0x86]     ; Store to memory
    
    ; Set completion flag
    LD A, #0xFF      ; Success value
    ST A, [0x8F]     ; Store at memory location 0x8F

    ; Trigger the print_uart_buffer function
    LD A, #0x01      ; Value to trigger printing
    ST A, [0xE0]     ; Set the UART buffer print trigger
    
    HLT              ; End program
