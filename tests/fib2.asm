LD A, #0x01       ; Initialize first Fibonacci number
LD B, #0x01       ; Initialize second Fibonacci number

; Store first two numbers
ST A, [0x91]      ; Store 1 at address 0x91
ST B, [0x92]      ; Store 1 at address 0x92

; Calculate and store next 6 Fibonacci numbers (as you already had)
ADD C, A, B       ; C = A + B (fib3 = fib1 + fib2 = 2)
ST C, [0x93]      ; Store 2 at address 0x93

LD A, B           ; A = B (A becomes fib2 = 1)
LD B, C           ; B = C (B becomes fib3 = 2)

ADD C, A, B       ; C = A + B (fib4 = fib2 + fib3 = 1+2 = 3)
ST C, [0x94]      ; Store 3 at address 0x94

LD A, B           ; Shift values forward (A = 2)
LD B, C           ; (B = 3)

ADD C, A, B       ; C = A + B (fib5 = 2+3 = 5)
ST C, [0x95]      ; Store 5 at address 0x95

LD A, B           ; A = 3
LD B, C           ; B = 5

ADD C, A, B       ; C = A + B (fib6 = 3+5 = 8)
ST C, [0x96]      ; Store 8 at address 0x96

LD A, B           ; A = 5
LD B, C           ; B = 8

ADD C, A, B       ; C = A + B (fib7 = 5+8 = 13)
ST C, [0x97]      ; Store 13 at address 0x97

LD A, B           ; A = 8
LD B, C           ; B = 13

ADD C, A, B       ; C = A + B (fib8 = 8+13 = 21)
ST C, [0x98]      ; Store 21 at address 0x98

; Continue for more Fibonacci numbers to reach 0xD
LD A, B           ; A = 13
LD B, C           ; B = 21

ADD C, A, B       ; C = A + B (fib9 = 13+21 = 34)
ST C, [0x99]      ; Store 34 at address 0x99

LD A, B           ; A = 21
LD B, C           ; B = 34

ADD C, A, B       ; C = A + B (fib10 = 21+34 = 55)
ST C, [0x9A]      ; Store 55 at address 0x9A

LD A, B           ; A = 34
LD B, C           ; B = 55

ADD C, A, B       ; C = A + B (fib11 = 34+55 = 89)
ST C, [0x9B]      ; Store 89 at address 0x9B

LD A, B           ; A = 55
LD B, C           ; B = 89

ADD C, A, B       ; C = A + B (fib12 = 55+89 = 144)
ST C, [0x9C]      ; Store 144 at address 0x9C

LD A, B           ; A = 89
LD B, C           ; B = 144

ADD C, A, B       ; C = A + B (fib13 = 89+144 = 233)
ST C, [0x9D]      ; Store 233 at address 0x9D (this is 0xD in hexadecimal)

HLT               ; Halt the program
