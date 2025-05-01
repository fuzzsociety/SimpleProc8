# SimpleProc8 Binary Ninja Plugin

## Overview

This plugin adds support for the SimpleProc-8 processor architecture in Binary Ninja, enabling reverse engineering and analysis of SimpleProc-8 binaries. The SimpleProc-8 is a simple 8-bit processor with 4 registers, 256 bytes of addressable memory, and a straightforward instruction set.

## Architecture Specifications

The SimpleProc-8 processor has the following specifications:

- **Address Space**: 8-bit (256 bytes of memory)
- **Registers**: 4 general-purpose registers (A, B, C, D)
- **Flags**: 4 status flags (Zero, Carry, Negative, Overflow)
- **Instruction Size**: 1-2 bytes
- **File Extension**: `.zz`

## Plugin Components

The plugin consists of two main components:

1. **SimpleProc8 Architecture Class**: Defines the instruction set and register layout
2. **SimpleProc8View Class**: Handles the binary file loading and memory layout

### Instruction Set

The SimpleProc-8 instruction set includes:

| Opcode | Mnemonic | Description | Format |
|--------|----------|-------------|--------|
| 0x0    | LD       | Load value  | `LD Rx, #val` / `LD Rx, [addr]` / `LD Rx, [B]` / `LD Rx, Ry` |
| 0x1    | ST       | Store value | `ST Rx, [addr]` / `ST Rx, [B]` |
| 0x2    | ADD      | Add         | `ADD Rx, Ry` |
| 0x3    | SUB      | Subtract    | `SUB Rx, Ry` |
| 0x4    | INC      | Increment   | `INC Rx` |
| 0x5    | DEC      | Decrement   | `DEC Rx` |
| 0x6    | AND      | Logical AND | `AND Rx, Ry` |
| 0x7    | OR       | Logical OR  | `OR Rx, Ry` |
| 0x8    | XOR      | Logical XOR | `XOR Rx, Ry` |
| 0x9    | NOT      | Logical NOT | `NOT Rx` |
| 0xA    | JMP      | Jump        | `JMP addr` / `JMP [Rx]` |
| 0xB    | JZ       | Jump if Zero| `JZ addr` |
| 0xC    | JNZ      | Jump if Not Zero | `JNZ addr` |
| 0xD    | JC       | Jump if Carry | `JC addr` |
| 0xE    | NOP      | No Operation | `NOP` |
| 0xF    | HLT      | Halt        | `HLT` |

## Memory Layout

The default memory layout assumed by the plugin:

- **0x00-0x7F**: Code segment (128 bytes)
- **0x80-0xFD**: Data segment (126 bytes)
- **0xFE-0xFF**: Special variables (2 bytes)

## How the Plugin Works

### Instruction Decoding

The plugin decodes SimpleProc-8 instructions by:

1. Extracting the opcode (upper 4 bits)
2. Extracting the register identifier (bits 2-3)
3. Extracting the addressing mode (lower 2 bits)
4. Determining instruction length (1-2 bytes)
5. Identifying branch targets for control flow analysis

### Binary View

When loading a `.zz` file, the SimpleProc8View:

1. Identifies the file as a SimpleProc-8 binary based on the `.zz` extension
2. Creates appropriate memory segments for code and data
3. Adds an entry point at address 0x00
4. Analyzes the binary to identify functions
5. Configures data types for array storage (0x80-0xBF) and variables (0xFE-0xFF)

### Disassembly

The disassembler generates human-readable assembly code with:

- Proper register names (a, b, c, d)
- Immediate values with '#' prefix
- Memory references with square brackets
- Correct operand formatting for each instruction type

### Low Level IL

The plugin provides low-level intermediate language (LLIL) support for key instructions to enable Binary Ninja's advanced analysis features, including:

- Register assignments
- Memory loads and stores
- Arithmetic operations
- Jumps and branches

## Usage

1. Install the plugin in your Binary Ninja plugins directory
2. Open a SimpleProc-8 binary (`.zz` file)
3. Binary Ninja will automatically recognize and analyze the file
4. Use Binary Ninja's standard analysis tools to explore the code

## Benefits

- **Visual Analysis**: See the control flow graph of SimpleProc-8 programs
- **Cross-References**: Track register and memory usage throughout the program
- **Symbolic Execution**: Leverage Binary Ninja's analysis capabilities
- **Documentation**: Add comments and annotations to the disassembly

## Example

When analyzing a SimpleProc-8 binary containing the bubble sort algorithm, Binary Ninja will show:

- The main code section with proper disassembly
- The array memory section (0x80-0xBF)
- Control flow for the sorting algorithm with nested loops
- Register usage and data flow

## Limitations

- Limited support for stack operations (SimpleProc-8 doesn't have a hardware stack)
- Flag behavior is simplified in the LLIL implementation
- No decompiler support for higher-level pseudocode generation

## Development

The plugin is designed to be extensible for future enhancements, such as:

- Adding more sophisticated analysis of flag behavior
- Supporting custom Binary Ninja views for SimpleProc-8 specific data
- Implementing additional helper functions for SimpleProc-8 analysis
