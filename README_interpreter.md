# SimpleProc8 Interpreter Explained

The SimpleProc8 interpreter simulates an 8-bit processor with 4 registers, 256 bytes of memory, and a simple instruction set. Let me walk you through how it works.

## Core Architecture

```python
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
```

The constructor initializes the processor state:
- Four 8-bit registers (`A`, `B`, `C`, `D`)
- A program counter (`pc`) for tracking the current instruction
- Status flags that affect program flow
- 256 bytes of memory (addresses 0x00-0xFF)

## Loading Programs

```python
def load_program(self, program):
    """Load a program into memory."""
    if isinstance(program, str):
        # Convert hex string program to bytes
        program = [int(x, 16) for x in program.split()]

    for i, byte in enumerate(program):
        if i < 256:  # Ensure we don't exceed memory bounds
            self.memory[i] = byte & 0xFF  # Ensure byte is 8-bit
```

This function loads a program into memory, either from a list of bytes or a space-separated hex string. It ensures each value is a valid 8-bit number (0-255).

```python
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
```

This function loads a program from a binary file, handling any errors that might occur during loading.

## Instruction Execution Cycle

```python
def fetch(self):
    """Fetch the next byte from memory."""
    byte = self.memory[self.pc]
    self.pc = (self.pc + 1) & 0xFF  # Ensure PC wraps at 256
    return byte
```

The `fetch` function gets the next instruction byte from memory at the current program counter position and increments the program counter. The bitwise `& 0xFF` operation ensures the program counter wraps around when it exceeds 255, keeping it in the valid 8-bit range.

```python
def decode(self, instruction):
    """Decode an instruction into opcode and operands."""
    opcode = (instruction >> 4) & 0x0F
    reg = (instruction >> 2) & 0x03
    mode = instruction & 0x03

    return opcode, reg, mode
```

The `decode` function extracts the components of an instruction:
- The 4-bit opcode (bits 7-4)
- The 2-bit register code (bits 3-2)
- The 2-bit addressing mode (bits 1-0)

```python
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
```

The `execute` function first decodes the instruction, then calls the appropriate handler function based on the opcode. The handler functions are stored in the `self.opcodes` dictionary.

## Processor Control

```python
def run(self, start_addr=0, max_instructions=200):
    """Run the processor from a starting address."""
    self.pc = start_addr
    self.running = True
    self.instruction_count = 0

    while self.running and self.instruction_count < max_instructions:
        instruction = self.fetch()
        self.execute(instruction)
        self.instruction_count += 1
        self.dump_memory(0x80, 0x99)

    if self.instruction_count >= max_instructions:
        print(f"Execution stopped: Maximum instructions ({max_instructions}) exceeded.")

    return self.instruction_count
```

The `run` function implements the main execution loop:
1. Set the program counter to the start address
2. Repeatedly fetch, decode, and execute instructions 
3. Stop when either the program halts (`self.running = False`) or the maximum instruction count is reached
4. Return the total number of instructions executed

```python
def step(self):
    """Execute a single instruction."""
    if self.running:
        instruction = self.fetch()
        self.execute(instruction)
        self.instruction_count += 1
        return True
    return False
```

The `step` function executes a single instruction, useful for debugging and step-by-step execution.

## Flag Management

```python
def _update_flags(self, result):
    """Update processor flags based on result."""
    # Zero flag
    self.flags['Z'] = (result == 0)

    # Negative flag (bit 7 set)
    self.flags['N'] = ((result & 0x80) != 0)

    # Ensure result is 8-bit
    return result & 0xFF
```

This helper function updates processor flags based on a result value:
- Sets the Zero flag (`Z`) if the result is zero
- Sets the Negative flag (`N`) if bit 7 is set (the 8-bit signed number is negative)
- Masks the result to 8 bits to ensure it's a valid 8-bit value

## Instruction Handlers

### Load Operation

```python
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

    elif mode == 0b11:  # Register-to-register
        reg2_code = self.fetch()
        reg2_name = self._get_register(reg2_code)
        self.registers[reg_name] = self.registers[reg2_name]
        if self.debug:
            print(f"LD {reg_name}, {reg2_name}")
```

The Load (`LD`) instruction loads a value into a register using four different addressing modes:
- **Immediate mode**: Load a constant value (next byte in memory)
- **Direct mode**: Load from a memory address (specified by next byte)
- **Register indirect**: Load from the memory address in register B
- **Register-to-register**: Copy value from another register

### Store Operation

```python
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
```

The Store (`ST`) instruction stores a register value into memory using two addressing modes:
- **Direct mode**: Store to a specific memory address (specified by next byte)
- **Register indirect**: Store to the memory address in register B

### Arithmetic Operations

```python
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
```

The Add (`ADD`) instruction adds the value of a second register to the first register:
- Sets the Carry flag if the result exceeds 255 (unsigned overflow)
- Sets the Overflow flag for signed overflow (when adding two positive numbers gives a negative result, or vice versa)

```python
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
```

The Subtract (`SUB`) instruction subtracts the value of a second register from the first register:
- Sets the Carry flag if the result is negative in unsigned context
- Sets the Overflow flag for signed subtraction overflow
- The carry flag is particularly important for implementing comparisons and conditional jumps

### Increment and Decrement

```python
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
```

The Increment (`INC`) instruction adds 1 to a register value, setting flags appropriately.

```python
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
```

The Decrement (`DEC`) instruction subtracts 1 from a register value, setting flags appropriately.

### Logical Operations

```python
def _and(self, reg, operand):
    """AND operation: AND Rx, Ry"""
    reg_name = self._get_register(reg)
    operand_name = self._get_register(operand)

    result = self.registers[reg_name] & self.registers[operand_name]

    # Update flags and store result
    self.registers[reg_name] = self._update_flags(result)

    if self.debug:
        print(f"AND {reg_name}, {operand_name}")
```

The `AND` instruction performs a bitwise AND between two registers.

```python
def _or(self, reg, operand):
    """OR operation: OR Rx, Ry"""
    reg_name = self._get_register(reg)
    operand_name = self._get_register(operand)

    result = self.registers[reg_name] | self.registers[operand_name]

    # Update flags and store result
    self.registers[reg_name] = self._update_flags(result)

    if self.debug:
        print(f"OR {reg_name}, {operand_name}")
```

The `OR` instruction performs a bitwise OR between two registers.

```python
def _xor(self, reg, operand):
    """XOR operation: XOR Rx, Ry"""
    reg_name = self._get_register(reg)
    operand_name = self._get_register(operand)

    result = self.registers[reg_name] ^ self.registers[operand_name]

    # Update flags and store result
    self.registers[reg_name] = self._update_flags(result)

    if self.debug:
        print(f"XOR {reg_name}, {operand_name}")
```

The `XOR` instruction performs a bitwise exclusive OR between two registers.

```python
def _not(self, reg, _):
    """NOT operation: NOT Rx"""
    reg_name = self._get_register(reg)

    result = ~self.registers[reg_name] & 0xFF  # Bitwise NOT with 8-bit mask

    # Update flags and store result
    self.registers[reg_name] = self._update_flags(result)

    if self.debug:
        print(f"NOT {reg_name}")
```

The `NOT` instruction performs a bitwise NOT on a register value.

### Jump Operations

```python
def _jmp(self, reg, mode):
    """Jump operation: JMP addr"""
    if mode == 0b00:  # Direct
        addr = self.fetch()
        if self.debug:
            print(f"JMP 0x{addr:02X}")
        # Set PC directly to the jump target
        self.pc = addr

    elif mode == 0b01:  # Register indirect
        reg_name = self._get_register(reg)
        addr = self.registers[reg_name]
        if self.debug:
            print(f"JMP [{reg_name}]")
        # Set PC directly to the address in the register
        self.pc = addr
```

The Jump (`JMP`) instruction changes the program counter to a new address:
- **Direct mode**: Jump to a fixed address specified in the next byte
- **Register indirect**: Jump to the address contained in a register

```python
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
```

The Jump if Zero (`JZ`) instruction jumps to a specified address if the Zero flag is set.

```python
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
```

The Jump if Not Zero (`JNZ`) instruction jumps to a specified address if the Zero flag is not set.

```python
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
```

The Jump if Carry (`JC`) instruction jumps to a specified address if the Carry flag is set.

### Miscellaneous Operations

```python
def _nop(self, _, __):
    """No operation: NOP"""
    if self.debug:
        print("NOP")
```

The No Operation (`NOP`) instruction does nothing except consume a clock cycle.

```python
def _hlt(self, _, __):
    """Halt operation: HLT"""
    self.running = False
    if self.debug:
        print("HLT")
```

The Halt (`HLT`) instruction stops program execution by setting `self.running` to `False`.

## Debugging Utilities

```python
def dump_registers(self):
    """Print the current state of all registers."""
    print("Registers:")
    for reg, value in self.registers.items():
        print(f"  {reg}: 0x{value:02X} ({value})")

    flags_str = ''.join([flag if val else '-' for flag, val in self.flags.items()])
    print(f"Flags: [{flags_str}]")
    print(f"PC: 0x{self.pc:02X}")
```

The `dump_registers` function prints the current state of all registers, status flags, and the program counter.

```python
def dump_memory(self, start=0, end=16):
    """Print a section of memory."""
    print(f"Memory (0x{start:02X}-0x{end-1:02X}):")
    for i in range(start, end, 16):
        row = self.memory[i:i+16]
        hex_values = ' '.join([f"{val:02X}" for val in row])
        print(f"  0x{i:02X}: {hex_values}")
```

The `dump_memory` function prints a section of memory in a hex dump format.

```python
def disassemble(self, start=0, length=16):
    """Disassemble a section of memory."""
    print(f"Disassembly (0x{start:02X}-0x{start+length-1:02X}):")
    # ... (disassembly implementation details)
```

The `disassemble` function converts a section of memory back into assembly instructions, useful for debugging and examining loaded programs.

## Summary

The SimpleProc8 interpreter implements a complete virtual 8-bit processor with:

1. A fetch-decode-execute cycle
2. Four 8-bit registers
3. 256 bytes of memory
4. A rich set of instructions:
   - Data movement (LD, ST)
   - Arithmetic (ADD, SUB, INC, DEC)
   - Logical operations (AND, OR, XOR, NOT)
   - Flow control (JMP, JZ, JNZ, JC, NOP, HLT)
5. Status flags to track results of operations
6. Various addressing modes for flexible memory access
7. Debugging capabilities

This creates a functional but simple processor that demonstrates the core concepts of computer architecture while being accessible enough to understand fully.