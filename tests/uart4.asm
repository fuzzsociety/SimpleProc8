; UART Echo Test for SimpleProc-8
; Sends 0x41 ('A') and 0x42 ('B') and checks if we can get the response
; MMIO Memory layout:
; 0xF1: UART control register
; 0xF8: UART TX register (write)
; 0xF9: UART RX register (read)

start:
    ; Initialize UART
    LD A, #0x03      ; Enable both RX and TX interrupts
    ST A, [0xF1]     ; Store to control register
    
    ; Send first byte (0x41 - 'A')
    LD A, #0x41      ; A = 'A' (0x41)
    ST A, [0xF8]     ; Send via TX register
    
    ; Send second byte (0x42 - 'B')
    LD A, #0x42      ; A = 'B' (0x42)
    ST A, [0xF8]     ; Send via TX register
    
    ; Store expected responses for verification
    LD A, #0x41      ; ASCII 'A'
    ST A, [0x80]     ; Store at 0x80 (temporary storage)
    LD A, #0x42      ; ASCII 'B'
    ST A, [0x81]     ; Store at 0x81 (temporary storage)
    
    ; Wait for first echo (either using RX interrupt or polling)
    ; Since you mentioned echo, I'll assume we need to read back what we sent
wait_rx_1:
    LD A, [0xF9]     ; Read from RX register
    LD B, [0x80]     ; Load expected response ('A')
    SUB A, B         ; Compare received vs expected
    JZ rx_1_ok       ; If match, continue to next byte
    JMP wait_rx_1    ; Keep trying if no match
    
rx_1_ok:
    ; First byte received correctly, wait for second echo
    LD A, #0xAA      ; Success code for first byte
    ST A, [0x90]     ; Store success indicator
    
wait_rx_2:
    LD A, [0xF9]     ; Read from RX register
    LD B, [0x81]     ; Load expected response ('B')
    SUB A, B         ; Compare received vs expected
    JZ rx_2_ok       ; If match, we're done
    JMP wait_rx_2    ; Keep trying if no match
    
rx_2_ok:
    ; Both bytes received correctly
    LD A, #0xAA      ; Success code for second byte
    ST A, [0x91]     ; Store success indicator
    
    ; Overall success indicator
    LD A, #0x01      ; Success code
    ST A, [0xFF]     ; Store at 0xFF to indicate success
    
done:
    HLT              ; End programx