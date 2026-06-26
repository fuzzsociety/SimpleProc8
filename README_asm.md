# SimpleProc-8 Assembler Breakdown

The SimpleProc-8 assembler is a tool designed to convert SimpleProc-8 assembly code into binary machine code that can be executed by the SimpleProc-8 processor. This document breaks down how this assembler works, function by function.

## Core Components

### Initialization (`__init__`)

The assembler initializes with several important data structures:

- **Opcodes**: Maps assembly mnemonics to their 4-bit binary codes
- **Registers**: Maps register names (A, B, C, D) to their 2-bit codes
- **Addressing Modes**: Different modes for instructions like LD (load), ST (store), and JMP (jump)
- **Symbol Table**: Holds label-to-address mappings
- **Binary Output**: Stores the final assembled binary code

### Parsing Functions

#### `_parse_line(line)`
Parses a line of assembly code by:
- Removing comments (anything after `;`)
- Detecting labels (ending with `:`)
- Extracting the operation code (opcode) and operands
- Returning a structured representation of the instruction

#### `_parse_operand(operand)`
Analyzes an individual operand to determine its type:
- **Register**: `A`, `B`, `C`, `D`
- **Immediate value**: Preceded by `#` (e.g., `#42`, `#0xFF`)
- **Direct memory address**: Enclosed in brackets (e.g., `[0x80]`)
- **Indirect register access**: Register name in brackets (e.g., `[B]`)
- **Label**: Plain text reference to a code location

For `LD` and `ST`, a direct memory address may also be written **without** brackets — a bare number or label (e.g. `LD A, 0x80`, `ST A, count`). Because immediates always carry a `#`, a bare operand is unambiguous and is assembled to exactly the same bytes as the bracketed form. The bracketed style remains the recommended, more explicit convention.

## Two-Pass Assembly Process

### First Pass: Symbol Resolution (`_first_pass`)

The first pass scans through the entire assembly code to:
1. Build the symbol table by tracking labels and their corresponding addresses
2. Create an intermediate representation of the code
3. Calculate the size of each instruction to correctly calculate memory offsets

This is critical for resolving forward references (e.g., jumping to a label that appears later in the code).

```python
def _first_pass(self, assembly_code):
    # Process each line
    for line_num, line in enumerate(lines, 1):
        # Parse the line
        parsed = self._parse_line(line)
        
        # Handle labels and add to symbol table
        if parsed and parsed['type'] == 'label':
            self.symbol_table[parsed['name']] = binary_offset
            
        # Calculate instruction size and update offsets
        instruction_size = self._calculate_instruction_size(parsed)
        binary_offset += instruction_size
```

#### `_calculate_instruction_size(instruction)`
Determines how many bytes an instruction will occupy in the final binary:
- **Jump instructions** (`JMP`, `JZ`, `JNZ`, `JC`): Always 2 bytes (opcode + target address)
- **LD/ST with immediate/direct addressing**: 2 bytes (opcode + value/address)
- **LD/ST with register indirect**: 1 byte (just the opcode)
- **Most other instructions**: 1 byte

### Second Pass: Code Generation (`_second_pass`)

The second pass generates the actual binary code:
1. Uses the symbol table built in the first pass to resolve all label references
2. Converts each instruction into its binary representation
3. Tracks symbol references for debugging purposes

```python
def _second_pass(self):
    # Process each instruction in the intermediate representation
    for instruction in self.intermediate:
        # Assemble the instruction into binary
        binary_instruction = self._assemble_instruction(instruction)
        
        # Add to the final binary output
        self.binary.extend(binary_instruction)
```

#### `_assemble_instruction(instruction)`
This is the heart of the assembler, converting each parsed instruction into binary code:
1. Gets the binary opcode value
2. Handles different instruction formats based on the opcode type
3. Resolves symbol references using the symbol table
4. Returns the binary representation as a list of bytes

For example, for a `JMP` instruction:
```python
# JMP addr
inst_byte = (opcode << 4) | mode  # First byte: opcode + addressing mode
binary.append(inst_byte)
# Resolve address from symbol table if it's a label
if label_name in self.symbol_table:
    addr = self.symbol_table[label_name]
    binary.append(addr & 0xFF)  # Second byte: target address
```

## Instruction Encoding Details

### Basic Format
Instructions follow a general pattern:
- First 4 bits: Opcode
- Next 2 bits: Register or other parameter
- Last 2 bits: Addressing mode or secondary parameter

### Jump Instructions
All jump instructions (`JMP`, `JZ`, `JNZ`, `JC`) require 2 bytes:
- Byte 1: Opcode and addressing information
- Byte 2: Target address (either a direct value or resolved from a label)

### Load/Store Operations
- `LD Rx, #val` (load immediate): 2 bytes
- `LD Rx, [addr]` / `LD Rx, addr` (load direct, bracketed or bare): 2 bytes
- `LD Rx, [B]` (load indirect): 1 byte
- `LD Rx, Ry` (register-to-register): 2 bytes
- `ST Rx, [addr]` / `ST Rx, addr` (store direct, bracketed or bare): 2 bytes
- `ST Rx, [B]` (store indirect): 1 byte

The bracketed and bare direct forms assemble identically; both occupy 2 bytes, which `_calculate_instruction_size` accounts for so that label offsets stay consistent across the two passes.

### Register Operations
Most register operations like `ADD`, `SUB`, `INC`, etc. are 1 byte.

## Output and Debug Functions

The assembler provides various utility functions:
- `format_binary()`: Formats the binary output in different formats (hex, binary, etc.)
- `save_binary()`: Writes the binary to a file
- `save_symbol_map()`: Exports the symbol table
- `generate_debug_info()`: Creates detailed debugging information

## Complete Assembly Process

The complete assembly process happens through the main `assemble()` method:

```python
def assemble(self, assembly_code):
    self._first_pass(assembly_code)  # Build symbol table
    self._second_pass()              # Generate binary code
    return self.binary
```

The two-pass approach is essential for handling forward references to labels, ensuring that all symbols are resolved correctly regardless of where they appear in the code.# SimpleProc-8 Assembler Breakdown

