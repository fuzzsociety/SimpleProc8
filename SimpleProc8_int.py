import sys
import os

# Import the UART backend
try:
    from SimpleProc8_uart_back import UARTInterface
    uart_available = True
except ImportError:
    print("Warning: UART backend not available. UART functionality will be disabled.")
    uart_available = False

class SimpleProc8:
    """
    A simple interpreter for the SimpleProc-8 processor.

    The SimpleProc-8 is an 8-bit processor with:
    - 4 general-purpose registers (A, B, C, D)
    - 256 bytes of addressable memory
    - Simple instruction set
    """

    def __init__(self):
        # Initialize registers
        self.registers = {
            'A': 0,  # Register 00
            'B': 0,  # Register 01
            'C': 0,  # Register 02
            'D': 0   # Register 03
        }

        # Program Counter
        self.pc = 0

        # Flags (Zero, Carry, Negative, Overflow)
        self.flags = {
            'Z': False,
            'C': False,
            'N': False,
            'V': False
        }

        # Memory (256 bytes)
        self.memory = [0] * 256
        

        # MMIO region markers (used for internal tracking)
        self.mmio_start = 0xF0
        self.mmio_end = 0xFF
                
        # Initialize MMIO registers with clear separation of RX/TX
        self.memory[0xF0] = 0  # Status Register
                            # Bit 0: RX data available
                            # Bit 1: TX buffer empty
                            # Bit 7: IRQ pending

        self.memory[0xF1] = 0  # Interrupt Control
                            # Bit 0: RX interrupt enable
                            # Bit 1: TX interrupt enable
                            # Bit 7: Global interrupt enable

        # RX Buffer (4 bytes)
        self.memory[0xF2] = 0  # RX buffer[0]
        self.memory[0xF3] = 0  # RX buffer[1]
        self.memory[0xF4] = 0  # RX buffer[2]
        self.memory[0xF5] = 0  # RX buffer[3]
        self.memory[0xF6] = 0  # RX head pointer
        self.memory[0xF7] = 0  # RX tail pointer

        # TX Buffer (4 bytes)
        self.memory[0xF8] = 0  # TX data register
        self.memory[0xF9] = 0  # RX data register
        self.memory[0xFA] = 0  # TX buffer[0]
        self.memory[0xFB] = 0  # TX buffer[1]
        self.memory[0xFC] = 0  # TX buffer[2]
        self.memory[0xFD] = 0  # TX buffer[3]
        self.memory[0xFE] = 0  # TX head pointer
        self.memory[0xFF] = 0  # TX tail pointer

        
        # Interrupt flags
        self.irq_pending = False
        
        # UART connected status
        self.uart_connected = False

        # Interrupt flags
        self.irq_pending = False
        
        # Override memory accesses hook
        self.pre_memory_read = None
        self.post_memory_write = None
        

        # Running state
        self.running = True

        # Debug mode
        self.debug = True

        # Instruction count for statistics
        self.instruction_count = 0

        # Opcode mapping
        self.opcodes = {
            0b0000: self._ld,   # Load
            0b0001: self._st,   # Store
            0b0010: self._add,  # Add
            0b0011: self._sub,  # Subtract
            0b0100: self._inc,  # Increment
            0b0101: self._dec,  # Decrement
            0b0110: self._and,  # AND
            0b0111: self._or,   # OR
            0b1000: self._xor,  # XOR
            0b1001: self._not,  # NOT
            0b1010: self._jmp,  # Jump
            0b1011: self._jz,   # Jump if zero
            0b1100: self._jnz,  # Jump if not zero
            0b1101: self._jc,   # Jump if carry
            0b1110: self._nop,  # No operation
            0b1111: self._hlt   # Halt
        }

        # Register mapping
        self.reg_map = {
            0b00: 'A',
            0b01: 'B',
            0b10: 'C',
            0b11: 'D'
        }

    def _update_flags(self, result):
        """Update processor flags based on result."""
        # Zero flag
        self.flags['Z'] = (result == 0)

        # Negative flag (bit 7 set)
        self.flags['N'] = ((result & 0x80) != 0)

        # Ensure result is 8-bit
        return result & 0xFF

    def load_program(self, program):
        """Load a program into memory."""
        if isinstance(program, str):
            # Convert hex string program to bytes
            program = [int(x, 16) for x in program.split()]

        for i, byte in enumerate(program):
            if i < 256:  # Ensure we don't exceed memory bounds
                self.memory[i] = byte & 0xFF  # Ensure byte is 8-bit

    def load_binary_file(self, filename):
        """Load a binary file into memory."""
        try:
            with open(filename, 'rb') as f:
                program = list(f.read())
                self.load_program(program)
                return True
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            return False

    def fetch(self):
        """Fetch the next byte from memory."""
        # Process any pre-read actions for MMIO
        if self.pre_memory_read:
            self.pre_memory_read(self.pc)
        byte = self.memory[self.pc]
        self.pc = (self.pc + 1) & 0xFF  # Ensure PC wraps at 256
        return byte

    def decode(self, instruction):
        """Decode an instruction into opcode and operands."""
        opcode = (instruction >> 4) & 0x0F
        reg = (instruction >> 2) & 0x03
        mode = instruction & 0x03

        return opcode, reg, mode
    
    def print_uart_buffer(self):
        out = []
        if (self.irq_pending) and self.memory[0xE0] == 1:
            for i in range(3): #UART BUFFER is 4 bytes
                byte_value = self.memory[0xF2+i]
                # Convert integer to character
                char = chr(byte_value) if 32 <= byte_value <= 126 else f"\\x{byte_value:02x}"
                out.append(char)
            print(f"UART Received: {''.join(out)}")

    def _get_register(self, reg_code):
        """Get the register name from its code."""
        return self.reg_map.get(reg_code, 'A')  # Default to A if invalid

    def _ld(self, reg, mode):
        """Load operation: LD Rx, val/addr"""
        reg_name = self._get_register(reg)

        if mode == 0b00:  # Immediate
            value = self.fetch()
            self.registers[reg_name] = value
            if self.debug:
                print(f"LD {reg_name}, #{value}")

        elif mode == 0b01:  # Direct
            addr = self.fetch()
            
            # Process any pre-read MMIO actions
            if self.pre_memory_read:
                self.pre_memory_read(addr)        
            
            value = self.memory[addr]
            self.registers[reg_name] = value
            if self.debug:
                print(f"LD {reg_name}, [{addr}]")

        elif mode == 0b10:  # Register indirect
            addr = self.registers['B']
            
            # Process any pre-read MMIO actions
            if self.pre_memory_read:
                self.pre_memory_read(addr)    

            value = self.memory[addr]
            self.registers[reg_name] = value
            if self.debug:
                print(f"LD {reg_name}, [B]")

        elif mode == 0b11:  # Register-to-register (NEW)
            reg2_code = self.fetch()
            reg2_name = self._get_register(reg2_code)
            self.registers[reg_name] = self.registers[reg2_name]
            if self.debug:
                print(f"LD {reg_name}, {reg2_name}")

    def _st(self, reg, mode):
        """Store operation: ST Rx, addr"""
        reg_name = self._get_register(reg)
        value = self.registers[reg_name]

        if mode == 0b00:  # Direct
            addr = self.fetch()
            self.memory[addr] = value

            # Process any post-write MMIO actions
            if self.post_memory_write:
                self.post_memory_write(addr, value)

            if self.debug:
                print(f"ST {reg_name}, [{addr}]")

        elif mode == 0b01:  # Register indirect
            addr = self.registers['B']
            self.memory[addr] = value

            # Process any post-write MMIO actions
            if self.post_memory_write:
                self.post_memory_write(addr, value)

            if self.debug:
                print(f"ST {reg_name}, [B]")

    def _add(self, reg, operand):
        """Add operation: ADD Rx, Ry"""
        reg_name = self._get_register(reg)
        operand_name = self._get_register(operand)

        result = self.registers[reg_name] + self.registers[operand_name]

        # Set carry flag if result exceeds 8 bits
        self.flags['C'] = (result > 0xFF)

        # Handle overflow for signed addition
        a = self.registers[reg_name]
        b = self.registers[operand_name]
        self.flags['V'] = ((a & 0x80) == (b & 0x80)) and ((result & 0x80) != (a & 0x80))

        # Update flags and store result
        self.registers[reg_name] = self._update_flags(result)

        if self.debug:
            print(f"ADD {reg_name}, {operand_name}")

    def _sub(self, reg, operand):
        """Subtract operation: SUB Rx, Ry"""
        reg_name = self._get_register(reg)
        operand_name = self._get_register(operand)

        result = self.registers[reg_name] - self.registers[operand_name]

        # Set carry flag if result is negative in unsigned context
        self.flags['C'] = (result < 0)

        # Handle overflow for signed subtraction
        a = self.registers[reg_name]
        b = self.registers[operand_name]
        self.flags['V'] = ((a & 0x80) != (b & 0x80)) and ((result & 0x80) != (a & 0x80))

        # Update flags and store result
        self.registers[reg_name] = self._update_flags(result & 0xFF)

        if self.debug:
            print(f"SUB {reg_name}, {operand_name}")
            print(f"  Flag Z: {self.flags['Z']}, Flag C: {self.flags['C']}") # Debug flag state

    def _inc(self, reg, _):
        """Increment operation: INC Rx"""
        reg_name = self._get_register(reg)

        result = self.registers[reg_name] + 1

        # Set carry flag if result exceeds 8 bits
        self.flags['C'] = (result > 0xFF)

        # Handle overflow for signed addition
        a = self.registers[reg_name]
        self.flags['V'] = (a == 0x7F)  # Overflow when 0x7F + 1 = 0x80 (positive to negative)

        # Update flags and store result
        self.registers[reg_name] = self._update_flags(result)

        if self.debug:
            print(f"INC {reg_name}")

    def _dec(self, reg, _):
        """Decrement operation: DEC Rx"""
        reg_name = self._get_register(reg)

        result = self.registers[reg_name] - 1

        # Set carry flag if result is negative in unsigned context
        self.flags['C'] = (result < 0)

        # Handle overflow for signed subtraction
        a = self.registers[reg_name]
        self.flags['V'] = (a == 0x80)  # Overflow when 0x80 - 1 = 0x7F (negative to positive)

        # Update flags and store result
        self.registers[reg_name] = self._update_flags(result & 0xFF)

        if self.debug:
            print(f"DEC {reg_name}")

    def _and(self, reg, operand):
        """AND operation: AND Rx, Ry"""
        reg_name = self._get_register(reg)
        operand_name = self._get_register(operand)

        result = self.registers[reg_name] & self.registers[operand_name]

        # Update flags and store result
        self.registers[reg_name] = self._update_flags(result)

        if self.debug:
            print(f"AND {reg_name}, {operand_name}")

    def _or(self, reg, operand):
        """OR operation: OR Rx, Ry"""
        reg_name = self._get_register(reg)
        operand_name = self._get_register(operand)

        result = self.registers[reg_name] | self.registers[operand_name]

        # Update flags and store result
        self.registers[reg_name] = self._update_flags(result)

        if self.debug:
            print(f"OR {reg_name}, {operand_name}")

    def _xor(self, reg, operand):
        """XOR operation: XOR Rx, Ry"""
        reg_name = self._get_register(reg)
        operand_name = self._get_register(operand)

        result = self.registers[reg_name] ^ self.registers[operand_name]

        # Update flags and store result
        self.registers[reg_name] = self._update_flags(result)

        if self.debug:
            print(f"XOR {reg_name}, {operand_name}")

    def _not(self, reg, _):
        """NOT operation: NOT Rx"""
        reg_name = self._get_register(reg)

        result = ~self.registers[reg_name] & 0xFF  # Bitwise NOT with 8-bit mask

        # Update flags and store result
        self.registers[reg_name] = self._update_flags(result)

        if self.debug:
            print(f"NOT {reg_name}")

    def _jmp(self, reg, mode):
        """Jump operation: JMP addr"""
        if mode == 0b00:  # Direct
            addr = self.fetch()
            if self.debug:
                print(f"JMP 0x{addr:02X}")
            # Set PC directly to the jump target
            self.pc = addr

        elif mode == 0b01:  # Register indirect
            reg_name = self._get_register(reg)  # Use provided register, not always A
            addr = self.registers[reg_name]
            if self.debug:
                print(f"JMP [{reg_name}]")
            # Set PC directly to the address in the register
            self.pc = addr

    def _jz(self, _, __):
        """Jump if zero operation: JZ addr"""
        addr = self.fetch()

        if self.flags['Z']:
            if self.debug:
                print(f"JZ 0x{addr:02X} (Taken)")
            # Set PC directly to the jump target
            self.pc = addr
        elif self.debug:
            print(f"JZ 0x{addr:02X} (Not taken): Z flag is {self.flags['Z']}")

    def _jnz(self, _, __):
        """Jump if not zero operation: JNZ addr"""
        addr = self.fetch()

        if not self.flags['Z']:
            if self.debug:
                print(f"JNZ 0x{addr:02X} (Taken)")
            # Set PC directly to the jump target
            self.pc = addr
        elif self.debug:
            print(f"JNZ 0x{addr:02X} (Not taken): Z flag is {self.flags['Z']}")

    def _jc(self, _, __):
        """Jump if carry operation: JC addr"""
        addr = self.fetch()

        if self.flags['C']:
            if self.debug:
                print(f"JC 0x{addr:02X} (Taken)")
            # Set PC directly to the jump target
            self.pc = addr
        elif self.debug:
            print(f"JC 0x{addr:02X} (Not taken): C flag is {self.flags['C']}")

    def _nop(self, _, __):
        """No operation: NOP"""
        if self.debug:
            print("NOP")

    def _hlt(self, _, __):
        """Halt operation: HLT"""
        self.running = False
        if self.debug:
            print("HLT")

    def execute(self, instruction):
        """Execute a decoded instruction."""
        opcode, reg, mode = self.decode(instruction)

        if self.debug:
            print(f"Executing instruction at 0x{(self.pc-1) & 0xFF:02X}: 0x{instruction:02X} (OP: {opcode:X}, REG: {reg:X}, MODE: {mode:X})")

        # Call the appropriate opcode handler
        if opcode in self.opcodes:
            self.opcodes[opcode](reg, mode)
        else:
            print(f"Error: Unknown opcode 0x{opcode:X}")
            self.running = False

        if self.debug:
            self.dump_registers()
            print("") # Extra line for readability
            print("\nMMIO Region (UART):")
            self.dump_memory(0xF0, 0x100)

    def debugger(self, instruction):
        opcode, reg, mode = self.decode(instruction)
        self.dump_registers()
        self.dump_memory(0x80, 0x99)

        if self.debug:
            print(f"Executing instruction at 0x{(self.pc-1) & 0xFF:02X}: 0x{instruction:02X} (OP: {opcode:X}, REG: {reg:X}, MODE: {mode:X})")
        
        while True:
            cmd = input("\nDebugger command (s/r/m/d/c/q)").strip().lower()
            if cmd == 's' or cmd == '': #Step or repeat
                break
            elif cmd == 'r': #show regs
                self.dump_registers()
            elif cmd == 'm': # show memory dump
                parts = cmd.split()
                start = 0x80
                end = 0x9F
                if len(parts) > 1:
                    try:
                        start = int(parts[1], 0)
                    except ValueError:
                        print("invalid starting address")
                if len(parts) > 2:
                    try:
                        start = int(parts[2], 0)
                    except ValueError:
                        print("invalid ending address")
                self.dump_memory()

            elif cmd.startswith('d'): #disas
                start = (self.pc-1) & 0xFF #align it to 8 bit instruction
                length = 16
                self.disassemble(start, length)
            elif cmd.startswith('c'):
                self.debug = False
                print("Continuing...")
                break

    def handle_mmio_read(self, address):
        """Handle MMIO region read access."""
        # Only process MMIO region
        if self.mmio_start <= address <= self.mmio_end:
            # Handle special MMIO reads
            if address == 0xF0:  # UART Status
                # Update status based on buffer state
                head = self.memory[0xF6]
                tail = self.memory[0xF7]
                
                # Check if data is available in buffer
                if head != tail:
                    self.memory[0xF0] |= 0x01  # Set RX ready bit
                else:
                    self.memory[0xF0] &= ~0x01  # Clear RX ready bit
                    
                # Always set TX ready bit (simplified for this implementation)
                self.memory[0xF0] |= 0x02
                
            elif address == 0xF9:  # UART RX Data
                # Read from circular buffer
                head = self.memory[0xF6]
                tail = self.memory[0xF7]
                
                if head != tail:
                    # Get data from buffer at tail position
                    buffer_idx = 0xF2 + (tail % 4)
                    data = self.memory[buffer_idx]
                    
                    # Update tail pointer with proper wrap-around
                    tail = (tail + 1) % 4
                    self.memory[0xF7] = tail
                    
                    # Store the read data in the RX register
                    self.memory[0xF9] = data
                    
                    # Update RX status if buffer empty after read
                    if head == tail:
                        self.memory[0xF0] &= ~0x01  # Clear RX ready bit
                    
                    if self.debug:
                        print(f"UART RX read: 0x{data:02X} ('{chr(data)}' if 32 <= data <= 126 else '')")
                else:
                    # No data available - return last value and don't change anything
                    if self.debug:
                        print("UART RX read attempted but no data available")

    def handle_mmio_write(self, address, value):
        """Handle MMIO region write access."""
        # Only process MMIO region
        if self.mmio_start <= address <= self.mmio_end:
            # Handle special MMIO writes
            if address == 0xF8:  # UART TX Data
                # Transmit data
                if self.debug:
                    print(f"UART TX: 0x{value:02X} ('{chr(value)}' if 32 <= value <= 126 else '')")
                
                # Signal to Python backend to send this data
                self.uart_tx_byte(value)
                
                # Set TX complete bit
                self.memory[0xF0] |= 0x02
                
                # If TX interrupt enabled, set pending
                if self.memory[0xF1] & 0x02:
                    self.memory[0xF0] |= 0x80  # Set IRQ pending
                    self.irq_pending = True

    def uart_rx_byte(self, byte):
        """Called by Python backend when data is received from UART."""
        # Get current head pointer
        head = self.memory[0xF6]
        tail = self.memory[0xF7]
        
        # Calculate next head position
        next_head = (head + 1) % 4
        
        # Check if buffer is full
        if next_head == tail:
            #if self.debug:
            #    print("UART buffer full, dropping byte")
            return False
        
        # Store in the appropriate buffer position
        buffer_idx = 0xF2 + (head % 4)
        self.memory[buffer_idx] = byte & 0xFF
        
        # Update head pointer with proper wrap-around
        self.memory[0xF6] = next_head
        
        # Set RX data available bit in status register
        self.memory[0xF0] |= 0x01
        
        # If RX interrupt enabled, set pending
        if self.memory[0xF1] & 0x01:
            self.memory[0xF0] |= 0x80  # Set IRQ pending bit
            self.irq_pending = True
        
        if self.debug:
            print(f"UART RX received: 0x{byte:02X} ('{chr(byte)}' if 32 <= byte <= 126 else '')")
        
        return True
    
    def uart_tx_byte(self, byte):
        """Transmit a byte over UART (to be implemented by backend)."""
        # This will be overridden by the Python backend
        pass

    def check_interrupts(self):
        """Check and handle any pending interrupts."""
        if self.irq_pending:
            # Check if global interrupts are enabled
            if self.memory[0xF1] & 0x80:
                # UART RX interrupt
                if (self.memory[0xF1] & 0x01) and (self.memory[0xF0] & 0x01):
                    # RX interrupt enabled and data available
                    return True
                    
                # UART TX interrupt
                if (self.memory[0xF1] & 0x02) and (self.memory[0xF0] & 0x02):
                    # TX interrupt enabled and TX ready
                    return True
                # Check for manual trigger of print_uart_buffer
            if self.memory[0xE0] == 1:
                self.print_uart_buffer()
        return False


    def run(self, start_addr=0, max_instructions=200):
        """MMIO HANDLERS"""
        self.pre_memory_read = self.handle_mmio_read
        self.post_memory_write = self.handle_mmio_write
        
        
        """Run the processor from a starting address."""
        self.pc = start_addr
        self.running = True
        self.instruction_count = 0

        while self.running and self.instruction_count < max_instructions:
            # Check for interrupts
            if self.check_interrupts():
            # Handle interrupt here if needed
                if self.debug:
                    print("Interrupt detected")    
            instruction = self.fetch()
            if self.debug:
                print("\n======= SimpleProc8 Interactive Debugger =======")
                print("Commands:")
                print("  s - Step (execute current instruction)")
                print("  r - Show registers")
                print("  m [start] [end] - Dump memory from start to end address")
                print("  d [start] [length] - Disassemble from start address")
                print("  c - Continue debugging") 
                print("  q - Quit debugger")
                print("=================================================\n")
                self.debugger(instruction)
            self.execute(instruction)
            self.instruction_count += 1

        if self.instruction_count >= max_instructions:
            print(f"Execution stopped: Maximum instructions ({max_instructions}) exceeded.")
        return self.instruction_count

    def step(self):
        """Execute a single instruction."""
        if self.running:
            instruction = self.fetch()
            self.execute(instruction)
            self.instruction_count += 1
            return True
        return False

    def dump_registers(self):
        """Print the current state of all registers."""
        print("Registers:")
        for reg, value in self.registers.items():
            print(f"  {reg}: 0x{value:02X} ({value})")

        flags_str = ''.join([flag if val else '-' for flag, val in self.flags.items()])
        print(f"Flags: [{flags_str}]")
        print(f"PC: 0x{self.pc:02X}")

    def dump_memory(self, start=0, end=16):
        """Print a section of memory."""
        print(f"Memory (0x{start:02X}-0x{end-1:02X}):")
        for i in range(start, end, 16):
            row = self.memory[i:i+16]
            hex_values = ' '.join([f"{val:02X}" for val in row])
            print(f"  0x{i:02X}: {hex_values}")

    def disassemble(self, start=0, length=16):
        """Disassemble a section of memory."""
        print(f"Disassembly (0x{start:02X}-0x{start+length-1:02X}):")

        # Save original PC
        original_pc = self.pc
        self.pc = start

        i = 0
        while i < length and self.pc < 256:
            addr = self.pc
            instruction = self.fetch()
            i += 1

            opcode, reg, mode = self.decode(instruction)
            reg_name = self._get_register(reg)
            mode_name = self._get_register(mode)

            # Simplified disassembly
            if opcode == 0b0000:  # LD
                if mode == 0b00 and self.pc < 256:  # Immediate
                    value = self.memory[self.pc]
                    self.pc = (self.pc + 1) & 0xFF
                    i += 1
                    print(f"  0x{addr:02X}: LD {reg_name}, #{value}")
                elif mode == 0b01 and self.pc < 256:  # Direct
                    addr_val = self.memory[self.pc]
                    self.pc = (self.pc + 1) & 0xFF
                    i += 1
                    print(f"  0x{addr:02X}: LD {reg_name}, [0x{addr_val:02X}]")
                elif mode == 0b10:  # Indirect
                    print(f"  0x{addr:02X}: LD {reg_name}, [B]")
                elif mode == 0b11 and self.pc < 256:  # Register-to-register
                    reg2_code = self.memory[self.pc]
                    reg2_name = self._get_register(reg2_code)
                    self.pc = (self.pc + 1) & 0xFF
                    i += 1
                    print(f"  0x{addr:02X}: LD {reg_name}, {reg2_name}")
            elif opcode == 0b0001:  # ST
                if mode == 0b00 and self.pc < 256:  # Direct
                    addr_val = self.memory[self.pc]
                    self.pc = (self.pc + 1) & 0xFF
                    i += 1
                    print(f"  0x{addr:02X}: ST {reg_name}, [0x{addr_val:02X}]")
                elif mode == 0b01:  # Indirect
                    print(f"  0x{addr:02X}: ST {reg_name}, [B]")
            elif opcode == 0b0010:  # ADD
                print(f"  0x{addr:02X}: ADD {reg_name}, {mode_name}")
            elif opcode == 0b0011:  # SUB
                print(f"  0x{addr:02X}: SUB {reg_name}, {mode_name}")
            elif opcode == 0b0100:  # INC
                print(f"  0x{addr:02X}: INC {reg_name}")
            elif opcode == 0b0101:  # DEC
                print(f"  0x{addr:02X}: DEC {reg_name}")
            elif opcode == 0b0110:  # AND
                print(f"  0x{addr:02X}: AND {reg_name}, {mode_name}")
            elif opcode == 0b0111:  # OR
                print(f"  0x{addr:02X}: OR {reg_name}, {mode_name}")
            elif opcode == 0b1000:  # XOR
                print(f"  0x{addr:02X}: XOR {reg_name}, {mode_name}")
            elif opcode == 0b1001:  # NOT
                print(f"  0x{addr:02X}: NOT {reg_name}")
            elif opcode == 0b1010:  # JMP
                if mode == 0b00 and self.pc < 256:  # Direct
                    addr_val = self.memory[self.pc]
                    self.pc = (self.pc + 1) & 0xFF
                    i += 1
                    print(f"  0x{addr:02X}: JMP 0x{addr_val:02X}")
                elif mode == 0b01:  # Indirect
                    print(f"  0x{addr:02X}: JMP [{reg_name}]")
            elif opcode == 0b1011 and self.pc < 256:  # JZ
                addr_val = self.memory[self.pc]
                self.pc = (self.pc + 1) & 0xFF
                i += 1
                print(f"  0x{addr:02X}: JZ 0x{addr_val:02X}")
            elif opcode == 0b1100 and self.pc < 256:  # JNZ
                addr_val = self.memory[self.pc]
                self.pc = (self.pc + 1) & 0xFF
                i += 1
                print(f"  0x{addr:02X}: JNZ 0x{addr_val:02X}")
            elif opcode == 0b1101 and self.pc < 256:  # JC
                addr_val = self.memory[self.pc]
                self.pc = (self.pc + 1) & 0xFF
                i += 1
                print(f"  0x{addr:02X}: JC 0x{addr_val:02X}")
            elif opcode == 0b1110:  # NOP
                print(f"  0x{addr:02X}: NOP")
            elif opcode == 0b1111:  # HLT
                print(f"  0x{addr:02X}: HLT")
            else:
                print(f"  0x{addr:02X}: Unknown (0x{instruction:02X})")

        # Restore original PC
        self.pc = original_pc


# Main function to handle command line arguments
def main():
    # Check if a filename is provided as command line argument
    if len(sys.argv) < 2:
        print("Usage: python simpleproc8.py <program.zz> [--debug] [--uart-device <device>]")
        sys.exit(1)

    binary_file = sys.argv[1]

    # Check if debug mode is enabled
    debug_mode = False
    uart_device = '/dev/ttyZZ'  # Default UART device
    
    # Parse command line arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--debug":
            debug_mode = True
        elif sys.argv[i] == "--uart-device" and i + 1 < len(sys.argv):
            uart_device = sys.argv[i + 1]
            i += 1  # Skip the next argument
        i += 1

    # Check if the binary file exists
    if not os.path.exists(binary_file):
        print(f"Error: Binary file '{binary_file}' not found.")
        sys.exit(1)

    # Create the processor
    cpu = SimpleProc8()
    cpu.debug = debug_mode

    # Set up UART backend
    try:
        from SimpleProc8_uart_back import UARTInterface
        uart = UARTInterface(cpu, uart_device=uart_device)
        uart_connected = uart.connect()
        if uart_connected:
            print(f"UART connected to {uart_device}")
        else:
            print(f"Warning: Failed to connect to UART device {uart_device}")
            uart = None
    except ImportError:
        print("Warning: UART backend not available. UART functionality will be disabled.")
        uart = None
    except Exception as e:
        print(f"Error setting up UART: {str(e)}")
        uart = None

    # Load the binary
    if not cpu.load_binary_file(binary_file):
        print("Failed to load binary file.")
        sys.exit(1)

    # Show the loaded program
    print("Program disassembly:")
    cpu.disassemble(0, 32)  # Show first 32 bytes

    try:
        # Run the program
        print("\nExecuting program...")
        cpu.run(max_instructions=1500)
        print("\nFinal state:")
        cpu.dump_registers()
        cpu.dump_memory(0x80, 0x100)  # Show memory region with results
        
        # Show MMIO region if UART was used
        if uart:
            print("\nMMIO Region (UART):")
            cpu.dump_memory(0xF0, 0x100)
        
        print(f"\nTotal instructions executed: {cpu.instruction_count}")
        
    finally:
        # Clean up UART if connected
        if uart:
            uart.disconnect()


if __name__ == "__main__":
    main()