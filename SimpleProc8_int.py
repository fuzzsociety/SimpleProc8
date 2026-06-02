import sys
import os

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
        byte = self.memory[self.pc]
        self.pc = (self.pc + 1) & 0xFF  # Ensure PC wraps at 256
        return byte

    def decode(self, instruction):
        """Decode an instruction into opcode and operands."""
        opcode = (instruction >> 4) & 0x0F
        reg = (instruction >> 2) & 0x03
        mode = instruction & 0x03

        return opcode, reg, mode

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
            value = self.memory[addr]
            self.registers[reg_name] = value
            if self.debug:
                print(f"LD {reg_name}, [{addr}]")

        elif mode == 0b10:  # Register indirect
            addr = self.registers['B']
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
            if self.debug:
                print(f"ST {reg_name}, [{addr}]")

        elif mode == 0b01:  # Register indirect
            addr = self.registers['B']
            self.memory[addr] = value
            if self.debug:
                print(f"ST {reg_name}, [B]")

    def _add(self, reg, mode):
        """Add operation: ADD Rx, Ry (2-operand) or ADD Rd, Rs1, Rs2 (3-operand)"""
        dest_name = self._get_register(reg)
        
        if mode == 0b11:  # 3-operand form: ADD Rd, Rs1, Rs2
            # Fetch the next byte which contains both source operands
            operand_byte = self.fetch()
            src1_code = (operand_byte >> 2) & 0x03  # Upper 2 bits for source 1
            src2_code = operand_byte & 0x03         # Lower 2 bits for source 2
            
            src1_name = self._get_register(src1_code)
            src2_name = self._get_register(src2_code)
            
            # For 3-operand: destination = source1 + source2
            result = self.registers[src1_name] + self.registers[src2_name]
            
            # Set carry flag if result exceeds 8 bits
            self.flags['C'] = (result > 0xFF)
            
            # Handle overflow for signed addition
            a = self.registers[src1_name]
            b = self.registers[src2_name]
            self.flags['V'] = ((a & 0x80) == (b & 0x80)) and ((result & 0x80) != (a & 0x80))
            
            if self.debug:
                print(f"ADD {dest_name}, {src1_name}, {src2_name}")
                
        else:  # 2-operand form: ADD Rx, Ry (Rx = Rx + Ry)
            src_name = self._get_register(mode)
            
            # For 2-operand: destination = destination + source
            result = self.registers[dest_name] + self.registers[src_name]
            
            # Set carry flag if result exceeds 8 bits
            self.flags['C'] = (result > 0xFF)
            
            # Handle overflow for signed addition
            a = self.registers[dest_name]
            b = self.registers[src_name]
            self.flags['V'] = ((a & 0x80) == (b & 0x80)) and ((result & 0x80) != (a & 0x80))
            
            if self.debug:
                print(f"ADD {dest_name}, {src_name}")

        # Update flags and store result
        self.registers[dest_name] = self._update_flags(result)

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

    def debugger(self, instruction):
        print("\n======= SimpleProc8 Interactive Debugger =======")
        print("Commands:")
        print("  s - Step (execute current instruction)")
        print("  r - Show registers")
        print("  m [start] [end] - Dump memory from start to end address")
        print("  d [start] [length] - Disassemble from start address")
        print("  c - Continue debugging") 
        print("  q - Quit debugger")
        print("=================================================\n")
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
            elif cmd.startswith('q'):
                self.running = False
                break
    def run(self, start_addr=0, max_instructions=200):
        """Run the processor from a starting address."""
        self.pc = start_addr
        self.running = True
        self.instruction_count = 0

        while self.running and self.instruction_count < max_instructions:
            instruction = self.fetch()
            if self.debug:
                self.debugger(instruction)
            self.execute(instruction)
            self.instruction_count += 1
            #self.dump_memory(0x80, 0x99)

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
                if mode == 0b11:  # 3-operand ADD: ADD Rd, Rs1, Rs2
                    if self.pc < 256:
                        operand_byte = self.memory[self.pc]
                        src1_code = (operand_byte >> 2) & 0x03
                        src2_code = operand_byte & 0x03
                        src1_name = self._get_register(src1_code)
                        src2_name = self._get_register(src2_code)
                        self.pc = (self.pc + 1) & 0xFF
                        i += 1
                        print(f"  0x{addr:02X}: ADD {reg_name}, {src1_name}, {src2_name}")
                    else:
                        print(f"  0x{addr:02X}: ADD {reg_name}, ???, ???")
                else:  # 2-operand ADD: ADD Rx, Ry
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
        print("Usage: python simpleproc8.py <program.zz> [--debug]")
        sys.exit(1)

    binary_file = sys.argv[1]

    # Check if debug mode is enabled
    debug_mode = False
    if len(sys.argv) > 2 and sys.argv[2] == "--debug":
        debug_mode = True

    # Check if the binary file exists
    if not os.path.exists(binary_file):
        print(f"Error: Binary file '{binary_file}' not found.")
        sys.exit(1)

    # Create the processor
    cpu = SimpleProc8()
    cpu.debug = debug_mode

    # Load the binary
    if not cpu.load_binary_file(binary_file):
        print("Failed to load binary file.")
        sys.exit(1)

    # Show the loaded program
    print("Program disassembly:")
    cpu.disassemble(0, 32)  # Show first 32 bytes

    # Run the program
    print("\nExecuting program...")
    cpu.run(max_instructions=1500)
    print("\nFinal state:")
    cpu.dump_registers()
    cpu.dump_memory(0x80, 0x100)  # Show memory region with results
    
    print(f"\nTotal instructions executed: {cpu.instruction_count}")


if __name__ == "__main__":
    main()
