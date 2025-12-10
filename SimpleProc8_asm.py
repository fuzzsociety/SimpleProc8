#!/usr/bin/env python3
import logging
import os
import sys


class SimpleProc8Assembler:
    """
    An assembler for the SimpleProc-8 processor.
    
    This assembler converts SimpleProc-8 assembly code into binary machine code
    based on the defined instruction format and encoding.
    """
    
    def __init__(self, debug=False):
        # Debug mode flag
        self.debug = debug
        
        # Set up logging
        if debug:
            # Configure logging to output to console
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(levelname)s: %(message)s',
                force=True  # Ensure our configuration takes precedence
            )
            # Force immediate output flush
            for handler in logging.getLogger().handlers:
                handler.flush = lambda: None
        else:
            logging.basicConfig(level=logging.INFO)
            
        self.logger = logging.getLogger('SimpleProc8Assembler')
        
        # Print startup message to verify execution
        if debug:
            print("DEBUG MODE ENABLED - Assembler Initialized")
        
        # Define opcodes
        self.opcodes = {
            'LD': 0b0000,
            'ST': 0b0001,
            'ADD': 0b0010,
            'SUB': 0b0011,
            'INC': 0b0100,
            'DEC': 0b0101,
            'AND': 0b0110,
            'OR': 0b0111,
            'XOR': 0b1000,
            'NOT': 0b1001,
            'JMP': 0b1010,
            'JZ': 0b1011,
            'JNZ': 0b1100,
            'JC': 0b1101,
            'NOP': 0b1110,
            'HLT': 0b1111
        }
        
        # Define registers
        self.registers = {
            'A': 0b00,
            'B': 0b01,
            'C': 0b10,
            'D': 0b11
        }
        
        # Addressing modes for LD
        self.ld_modes = {
            'immediate': 0b00,
            'direct': 0b01,
            'indirect': 0b10,
            'register': 0b11  # New mode for register-to-register transfers
        }
        
        # Addressing modes for ST
        self.st_modes = {
            'direct': 0b00,
            'indirect': 0b01
        }
        
        # Addressing modes for JMP
        self.jmp_modes = {
            'direct': 0b00,
            'indirect': 0b01
        }
        
        # Initialize symbol table for labels
        self.symbol_table = {}
        
        # Current address counter
        self.address = 0
        
        # Generated binary code
        self.binary = []
        
        # Intermediate representation for two-pass assembly
        self.intermediate = []
        
        # Store symbol references for later debug info
        self.symbol_references = []
        
        # Original assembly source lines (for debugging)
        self.source_lines = []
        
    def _debug_print(self, message):
        """Helper method to ensure debug messages are printed even if logging fails"""
        if self.debug:
            print(f"DEBUG: {message}")
            sys.stdout.flush()  # Force output to display immediately
        
    def _parse_operand(self, operand):
        """Parse an operand into its components."""
        if self.debug:
            self._debug_print(f"Parsing operand: {operand}")
            
        # Check if it's a register
        if operand in self.registers:
            return {'type': 'register', 'value': self.registers[operand]}
        
        # Check if it's an immediate value (decimal, hex, or binary)
        if operand.startswith('#'):
            value = operand[1:]
            if value.startswith('0x'):
                return {'type': 'immediate', 'value': int(value, 16)}
            elif value.startswith('0b'):
                return {'type': 'immediate', 'value': int(value, 2)}
            else:
                return {'type': 'immediate', 'value': int(value)}
        
        # Check if it's a memory reference [addr]
        if operand.startswith('[') and operand.endswith(']'):
            inner = operand[1:-1]
            
            # If it's a register (indirect)
            if inner in self.registers:
                return {'type': 'indirect', 'register': self.registers[inner]}
            
            # If it's a memory address
            if inner.startswith('0x'):
                return {'type': 'direct', 'address': int(inner, 16)}
            else:
                try:
                    return {'type': 'direct', 'address': int(inner)}
                except ValueError:
                    # It might be a label
                    return {'type': 'direct', 'label': inner}
        
        # Check if it's a direct address or label for jumps
        if operand.startswith('0x'):
            return {'type': 'address', 'value': int(operand, 16)}
        try:
            return {'type': 'address', 'value': int(operand)}
        except ValueError:
            # Must be a label
            return {'type': 'label', 'name': operand}
    
    def _parse_line(self, line):
        """Parse a line of assembly code."""
        # Remove comments
        if ';' in line:
            line = line[:line.index(';')]
        
        # Strip whitespace
        line = line.strip()
        
        # Skip empty lines
        if not line:
            return None
        
        # Check for labels
        label = None
        if ':' in line:
            parts = line.split(':', 1)
            label = parts[0].strip()
            line = parts[1].strip()
            
            # If line is empty after label, return just the label
            if not line:
                return {'type': 'label', 'name': label}
        
        # Split into opcode and operands
        parts = line.split()
        opcode = parts[0].upper()
        
        # Parse operands
        operands = []
        if len(parts) > 1:
            operand_str = ' '.join(parts[1:])
            # Split operands by comma, but handle square brackets
            in_brackets = False
            current_operand = ""
            for char in operand_str:
                if char == '[':
                    in_brackets = True
                    current_operand += char
                elif char == ']':
                    in_brackets = False
                    current_operand += char
                elif char == ',' and not in_brackets:
                    operands.append(current_operand.strip())
                    current_operand = ""
                else:
                    current_operand += char
            
            if current_operand:
                operands.append(current_operand.strip())
        
        # Return the parsed instruction
        return {
            'type': 'instruction',
            'label': label,
            'opcode': opcode,
            'operands': operands
        }

    def _first_pass(self, assembly_code):
        """First pass: build symbol table and intermediate representation."""
        lines = assembly_code.split('\n')
        self.source_lines = lines
        self.address = 0
        self.symbol_table = {}
        self.intermediate = []
        
        # Track both logical instruction address and binary offset
        binary_offset = 0
        
        if self.debug:
            self._debug_print("Starting first pass...")
        
        for line_num, line in enumerate(lines, 1):
            try:
                if self.debug:
                    self._debug_print(f"Processing line {line_num}: {line}")
                
                parsed = self._parse_line(line)
                
                # Skip empty lines and comments
                if not parsed:
                    continue
                
                # Handle labels
                if parsed['type'] == 'label':
                    # Use binary_offset for symbol table
                    self.symbol_table[parsed['name']] = binary_offset
                    if self.debug:
                        self._debug_print(f"Defined label '{parsed['name']}' at binary offset 0x{binary_offset:02X}")
                    continue
                
                # For instructions with a label, add to symbol table
                if parsed['label']:
                    # Use binary_offset for symbol table
                    self.symbol_table[parsed['label']] = binary_offset
                    if self.debug:
                        self._debug_print(f"Defined label '{parsed['label']}' at binary offset 0x{binary_offset:02X}")
                
                # Add line number and source text for debugging
                parsed['line_num'] = line_num
                parsed['source'] = line
                
                # Add to intermediate representation with both address trackers
                parsed['address'] = self.address  # Logical instruction address
                parsed['binary_offset'] = binary_offset  # Actual byte offset in binary
                self.intermediate.append(parsed)
                
                # Calculate instruction size - FIX: Make this match the actual assembly size
                instruction_size = self._calculate_instruction_size(parsed)
                
                self.address += 1  # Logical instruction count always increments by 1
                binary_offset += instruction_size  # Binary offset increments by actual instruction size
                
                if self.debug:
                    self._debug_print(f"Instruction size: {instruction_size} bytes, next binary offset: 0x{binary_offset:02X}")
                    self._debug_print(f"Logical instruction address: 0x{self.address:02X}")
                    
            except Exception as e:
                error_msg = f"Error on line {line_num}: {line}"
                self._debug_print(error_msg)
                self._debug_print(f"Exception: {str(e)}")
                raise SyntaxError(f"{error_msg}\n{str(e)}")
        
        # Print the symbol table for debugging
        if self.debug:
            self._debug_print("\nSymbol Table after first pass:")
            for label, addr in sorted(self.symbol_table.items(), key=lambda x: x[1]):
                self._debug_print(f"    Symbol reference: {label} -> 0x{addr:02X} (at offset +0)")

    def _calculate_instruction_size(self, instruction):
        """Calculate the size in bytes of an instruction."""
        opcode = instruction['opcode']
        operands = instruction.get('operands', [])
        
        # Default for most instructions is 1 byte
        size = 1
        
        if opcode == 'LD':
            if len(operands) < 2:
                return size  # Default to 1 byte if not enough operands
            
            # Get the destination register
            reg_name = operands[0]
            if reg_name not in self.registers:
                return size  # Default if invalid register
            
            # Parse second operand to determine addressing mode
            op2_str = operands[1]
            
            # Immediate mode LD Rx, #val - 2 bytes
            if op2_str.startswith('#'):
                return 2
                
            # Direct memory access LD Rx, [addr] - 2 bytes
            if op2_str.startswith('[') and op2_str.endswith(']'):
                inner = op2_str[1:-1]
                # If it's a register (indirect), it's 1 byte
                if inner in self.registers:
                    return 1
                # Otherwise it's a memory address, 2 bytes
                return 2
                
            # Register-to-register LD Rx, Ry - FIX: Always 2 bytes
            if op2_str in self.registers:
                return 2
                
        elif opcode == 'ST':
            if len(operands) < 2:
                return size
                
            # Parse second operand
            op2_str = operands[1]
            
            # Direct memory access ST Rx, [addr] - 2 bytes
            if op2_str.startswith('[') and op2_str.endswith(']'):
                inner = op2_str[1:-1]
                # If it's a register (indirect), it's 1 byte
                if inner in self.registers:
                    return 1
                # Otherwise it's a memory address, 2 bytes
                return 2
                
        elif opcode in ['JMP', 'JZ', 'JNZ', 'JC']:
            # Jump instructions always 2 bytes (opcode + target)
            return 2
            
        # All other instructions (ADD, SUB, INC, DEC, NOP, HLT, etc.) are 1 byte
        return size   

    def _first_passe(self, assembly_code):
        """First pass: build symbol table and intermediate representation."""
        lines = assembly_code.split('\n')
        self.source_lines = lines
        self.address = 0
        self.symbol_table = {}
        self.intermediate = []
        
        # Track both logical instruction address and binary offset
        binary_offset = 0
        
        if self.debug:
            self._debug_print("Starting first pass...")
        
        for line_num, line in enumerate(lines, 1):
            try:
                if self.debug:
                    self._debug_print(f"Processing line {line_num}: {line}")
                
                parsed = self._parse_line(line)
                from pprint import pprint

                # Skip empty lines and comments
                if not parsed:
                    continue
                
                # Handle labels
                if parsed['type'] == 'label':
                    # Use binary_offset for symbol table
                    self.symbol_table[parsed['name']] = binary_offset
                    if self.debug:
                        self._debug_print(f"Defined label '{parsed['name']}' at binary offset 0x{binary_offset:02X}")
                    continue
                
                # For instructions with a label, add to symbol table
                if parsed['label']:
                    # Use binary_offset for symbol table
                    self.symbol_table[parsed['label']] = binary_offset
                    if self.debug:
                        self._debug_print(f"Defined label '{parsed['label']}' at binary offset 0x{binary_offset:02X}")
                
                # Add line number and source text for debugging
                parsed['line_num'] = line_num
                parsed['source'] = line
                
                # Add to intermediate representation with both address trackers
                parsed['address'] = self.address  # Logical instruction address
                parsed['binary_offset'] = binary_offset  # Actual byte offset in binary
                self.intermediate.append(parsed)
                
                # Calculate instruction size
                instruction_size = 0
                
                if parsed['opcode'] in ['LD', 'ST']:
                    instruction_size = 1  # half byte opcode, half byte operand
                    
                    # Check if there's a second operand for memory access
                    if parsed['operands'] and len(parsed['operands']) > 1:
                        operand = self._parse_operand(parsed['operands'][1])
                        if operand['type'] in ['direct', 'immediate', 'address']:
                            instruction_size += 1  # Add another byte for address or immediate
                
                elif parsed['opcode'] in ['JMP', 'JZ', 'JNZ', 'JC']:
                    instruction_size = 2  # 1 byte opcode, 1 byte target address
                    
                else:
                    instruction_size = 1  # Single byte instructions
                
                self.address += 1  # Logical instruction count always increments by 1
                binary_offset += instruction_size  # Binary offset increments by actual instruction size
                
                if self.debug:
                    self._debug_print(f"Instruction size: {instruction_size} bytes, next binary offset: 0x{binary_offset:02X}")
                    self._debug_print(f"Logical instruction address: 0x{self.address:02X}")
                pprint(parsed)
                
            except Exception as e:
                error_msg = f"Error on line {line_num}: {line}"
                self._debug_print(error_msg)
                self._debug_print(f"Exception: {str(e)}")
                raise SyntaxError(f"{error_msg}\n{str(e)}")
        
        # Print the symbol table for debugging
        if self.debug:
            self._debug_print("\nSymbol Table after first pass:")
            for label, addr in sorted(self.symbol_table.items(), key=lambda x: x[1]):
                self._debug_print(f"    Symbol reference: {label} -> 0x{addr:02X} (at offset +0)")
    
    def _assemble_instruction(self, instruction):
        """Assemble a single instruction into binary code."""
        opcode = self.opcodes.get(instruction['opcode'])
        if opcode is None:
            raise SyntaxError(f"Unknown opcode: {instruction['opcode']}")
        
        binary = []
        symbol_refs = []  # Track symbol references in this instruction
        
        # Debug information
        if self.debug:
            addr_str = f"0x{instruction.get('address', 0):02X}"
            binary_offset_str = f"0x{instruction.get('binary_offset', 0):02X}"
            
            # Get opcode and operands safely
            opcode_str = instruction.get('opcode', '')
            operands = instruction.get('operands', [])
            operands_str = ' '.join(operands) if operands else ""
            
            self._debug_print(f"\nAssembling instruction at {addr_str} (binary offset {binary_offset_str}): {opcode_str} {operands_str}")
        
        # Handle different instruction types
        if instruction['opcode'] == 'LD':
            if len(instruction['operands']) < 2:
                raise SyntaxError(f"LD requires two operands: {instruction}")
            
            reg_name = instruction['operands'][0]
            if reg_name not in self.registers:
                raise SyntaxError(f"Invalid register: {reg_name}")
            
            reg = self.registers[reg_name]
            
            # Parse second operand to determine addressing mode
            op2 = self._parse_operand(instruction['operands'][1])
            
            if op2['type'] == 'immediate':
                # LD Rx, #val
                mode = self.ld_modes['immediate']
                inst_byte = (opcode << 4) | (reg << 2) | mode
                binary.append(inst_byte)
                binary.append(op2['value'] & 0xFF)
                
                if self.debug:
                    self._debug_print(f"LD {reg_name}, #{op2['value']} => {self.format_binary(binary, 'hex')}")
                
            elif op2['type'] == 'direct':
                # LD Rx, [addr]
                mode = self.ld_modes['direct']
                inst_byte = (opcode << 4) | (reg << 2) | mode
                binary.append(inst_byte)
                
                # Resolve address or label
                if 'address' in op2:
                    binary.append(op2['address'] & 0xFF)
                    if self.debug:
                        self._debug_print(f"LD {reg_name}, [0x{op2['address']:02X}] => {self.format_binary(binary, 'hex')}")
                elif 'label' in op2:
                    if op2['label'] in self.symbol_table:
                        addr = self.symbol_table[op2['label']]
                        binary.append(addr & 0xFF)
                        # Record symbol reference
                        symbol_refs.append({
                            'name': op2['label'],
                            'addr': instruction.get('binary_offset', 0) + 1,  # Byte after opcode
                            'resolved_to': addr
                        })
                        if self.debug:
                            self._debug_print(f"LD {reg_name}, [{op2['label']}] (resolved to [0x{addr:02X}]) => {self.format_binary(binary, 'hex')}")
                    else:
                        raise SyntaxError(f"Undefined label: {op2['label']}")
                        
            elif op2['type'] == 'indirect' and 'register' in op2 and op2['register'] == self.registers['B']:
                # LD Rx, [B]
                mode = self.ld_modes['indirect']
                inst_byte = (opcode << 4) | (reg << 2) | mode
                binary.append(inst_byte)
                if self.debug:
                    self._debug_print(f"LD {reg_name}, [B] => {self.format_binary(binary, 'hex')}")
                
            elif op2['type'] == 'register' and 'value' in op2:
                # LD Rx, Ry (register-to-register)
                reg2_value = op2['value']
                for reg2_name, reg2_val in self.registers.items():
                    if reg2_val == reg2_value:
                        src_reg_name = reg2_name
                        break
                
                # Use a custom encoding for register-to-register transfer
                inst_byte = (opcode << 4) | (reg << 2) | 0b11  # Using 0b11 as a special mode for reg-to-reg
                binary.append(inst_byte)
                binary.append(reg2_value & 0xFF)  # Store the register number in the second byte
                
                if self.debug:
                    self._debug_print(f"LD {reg_name}, {src_reg_name} => {self.format_binary(binary, 'hex')}")
                
            else:
                raise SyntaxError(f"Invalid addressing mode for LD: {instruction['operands'][1]}")
                
        elif instruction['opcode'] == 'ST':
            if len(instruction['operands']) < 2:
                raise SyntaxError(f"ST requires two operands: {instruction}")
            
            reg_name = instruction['operands'][0]
            if reg_name not in self.registers:
                raise SyntaxError(f"Invalid register: {reg_name}")
            
            reg = self.registers[reg_name]
            
            # Parse second operand for address
            op2 = self._parse_operand(instruction['operands'][1])
            
            if op2['type'] == 'direct':
                # ST Rx, [addr]
                mode = self.st_modes['direct']
                inst_byte = (opcode << 4) | (reg << 2) | mode
                binary.append(inst_byte)
                
                # Resolve address or label
                if 'address' in op2:
                    binary.append(op2['address'] & 0xFF)
                    if self.debug:
                        self._debug_print(f"ST {reg_name}, [0x{op2['address']:02X}] => {self.format_binary(binary, 'hex')}")
                elif 'label' in op2:
                    if op2['label'] in self.symbol_table:
                        addr = self.symbol_table[op2['label']]
                        binary.append(addr & 0xFF)
                        # Record symbol reference
                        symbol_refs.append({
                            'name': op2['label'],
                            'addr': instruction.get('binary_offset', 0) + 1,  # Byte after opcode
                            'resolved_to': addr
                        })
                        if self.debug:
                            self._debug_print(f"ST {reg_name}, [{op2['label']}] (resolved to [0x{addr:02X}]) => {self.format_binary(binary, 'hex')}")
                    else:
                        raise SyntaxError(f"Undefined label: {op2['label']}")
                        
            elif op2['type'] == 'indirect' and 'register' in op2 and op2['register'] == self.registers['B']:
                # ST Rx, [B]
                mode = self.st_modes['indirect']
                inst_byte = (opcode << 4) | (reg << 2) | mode
                binary.append(inst_byte)
                if self.debug:
                    self._debug_print(f"ST {reg_name}, [B] => {self.format_binary(binary, 'hex')}")
                
            else:
                raise SyntaxError(f"Invalid addressing mode for ST: {instruction['operands'][1]}")
                
        elif instruction['opcode'] in ['ADD', 'SUB', 'AND', 'OR', 'XOR']:
            if len(instruction['operands']) < 2:
                self._debug_print(f"{instruction['opcode']} requires at least two operands: {instruction}")
            
            """
            Check if it's 3-operand form (ADD Rd, Rs1, Rs2)
            For 3-Operand form instructions, ONLY register to register mode (0b11) is supported yet.
            """
            if len(instruction['operands']) == 3:
                dest_name = instruction['operands'][0]
                src1_name = instruction['operands'][1]  
                src2_name = instruction['operands'][2]
                
                if dest_name not in self.registers or src1_name not in self.registers or src2_name not in self.registers:
                    raise SyntaxError(f"Invalid register(s): {dest_name}, {src1_name}, {src2_name}")
                
                dest_reg = self.registers[dest_name]
                src1_reg = self.registers[src1_name]
                src2_reg = self.registers[src2_name]
                
                # Use mode 0b11 for 3-operand format
                inst_byte = (opcode << 4) | (dest_reg << 2) | 0b11
                binary.append(inst_byte)
                
                # Pack both source registers into next byte: src1 in upper 2 bits, src2 in lower 2 bits
                operands_byte = (src1_reg << 2) | src2_reg
                binary.append(operands_byte)
                
                if self.debug:
                    self._debug_print(f"{instruction['opcode']} {dest_name}, {src1_name}, {src2_name} => {self.format_binary(binary, 'hex')}")
                    
            else:
                # 2-operand form (ADD Rd, Rs)
                reg1_name = instruction['operands'][0]
                reg2_name = instruction['operands'][1]
                
                if reg1_name not in self.registers or reg2_name not in self.registers:
                    raise SyntaxError(f"Invalid register(s): {reg1_name}, {reg2_name}")
                
                reg1 = self.registers[reg1_name]
                reg2 = self.registers[reg2_name]
                
                inst_byte = (opcode << 4) | (reg1 << 2) | reg2
                binary.append(inst_byte)
                
                if self.debug:
                    self._debug_print(f"{instruction['opcode']} {reg1_name}, {reg2_name} => {self.format_binary(binary, 'hex')}")
            
        elif instruction['opcode'] in ['INC', 'DEC', 'NOT']:
            if len(instruction['operands']) < 1:
                raise SyntaxError(f"{instruction['opcode']} requires one operand: {instruction}")
            
            reg_name = instruction['operands'][0]
            
            if reg_name not in self.registers:
                raise SyntaxError(f"Invalid register: {reg_name}")
            
            reg = self.registers[reg_name]
            
            inst_byte = (opcode << 4) | (reg << 2)
            binary.append(inst_byte)
            
            if self.debug:
                self._debug_print(f"{instruction['opcode']} {reg_name} => {self.format_binary(binary, 'hex')}")
            
        elif instruction['opcode'] == 'JMP':
            if len(instruction['operands']) < 1:
                raise SyntaxError(f"JMP requires an operand: {instruction}")
            
            operand = self._parse_operand(instruction['operands'][0])
            
            if operand['type'] == 'address' or operand['type'] == 'label':
                # JMP addr
                mode = self.jmp_modes['direct']
                inst_byte = (opcode << 4) | mode
                binary.append(inst_byte)
                
                # Resolve address or label
                if 'value' in operand:
                    binary.append(operand['value'] & 0xFF)
                    if self.debug:
                        self._debug_print(f"JMP 0x{operand['value']:02X} => {self.format_binary(binary, 'hex')}")
                elif 'name' in operand:
                    if operand['name'] in self.symbol_table:
                        addr = self.symbol_table[operand['name']]
                        binary.append(addr & 0xFF)
                        # Record symbol reference
                        symbol_refs.append({
                            'name': operand['name'],
                            'addr': instruction.get('binary_offset', 0) + 1,  # Byte after opcode
                            'resolved_to': addr
                        })
                        if self.debug:
                            self._debug_print(f"JMP {operand['name']} (resolved to 0x{addr:02X}) => {self.format_binary(binary, 'hex')}")
                    else:
                        raise SyntaxError(f"Undefined label: {operand['name']}")
                        
            elif operand['type'] == 'indirect' and 'register' in operand:
                # JMP [Rx]
                mode = self.jmp_modes['indirect']
                inst_byte = (opcode << 4) | (operand['register'] << 2) | mode
                binary.append(inst_byte)
                
                for reg_name, reg_val in self.registers.items():
                    if reg_val == operand['register']:
                        jump_reg_name = reg_name
                        break
                
                if self.debug:
                    self._debug_print(f"JMP [{jump_reg_name}] => {self.format_binary(binary, 'hex')}")
                
            else:
                raise SyntaxError(f"Invalid addressing mode for JMP: {instruction['operands'][0]}")
                
        elif instruction['opcode'] in ['JZ', 'JNZ', 'JC']:
            if len(instruction['operands']) < 1:
                raise SyntaxError(f"{instruction['opcode']} requires an operand: {instruction}")
            
            operand = self._parse_operand(instruction['operands'][0])
            
            inst_byte = (opcode << 4)
            binary.append(inst_byte)
            
            # Resolve address or label
            if operand['type'] == 'address' and 'value' in operand:
                binary.append(operand['value'] & 0xFF)
                if self.debug:
                    self._debug_print(f"{instruction['opcode']} 0x{operand['value']:02X} => {self.format_binary(binary, 'hex')}")
            elif operand['type'] == 'label' and 'name' in operand:
                if operand['name'] in self.symbol_table:
                    target_addr = self.symbol_table[operand['name']]
                    binary.append(target_addr & 0xFF)
                    # Record symbol reference
                    symbol_refs.append({
                        'name': operand['name'],
                        'addr': instruction.get('binary_offset', 0) + 1,  # Byte after opcode
                        'resolved_to': target_addr
                    })
                    if self.debug:
                        self._debug_print(f"Parsing operand: {operand['name']}")
                        self._debug_print(f"{instruction['opcode']} {operand['name']} (resolved to 0x{target_addr:02X}) => 0x{inst_byte:02X} 0x{target_addr:02X}")
                else:
                    raise SyntaxError(f"Undefined label: {operand['name']}")
            else:
                raise SyntaxError(f"Invalid operand for {instruction['opcode']}: {instruction['operands'][0]}")
               
        elif instruction['opcode'] in ['NOP', 'HLT']:
            inst_byte = (opcode << 4)
            binary.append(inst_byte)
            
            if self.debug:
                self._debug_print(f"{instruction['opcode']} => {self.format_binary(binary, 'hex')}")
            
        else:
            raise SyntaxError(f"Unsupported instruction: {instruction['opcode']}")
        
        # Add any symbol references to our tracking list
        if symbol_refs:
            self.symbol_references.extend(symbol_refs)
            
        return binary
    
    def _second_pass(self):
        """Second pass: generate binary code using symbol table."""
        self.binary = []
        self.symbol_references = []
        binary_offset = 0
        
        if self.debug:
            self._debug_print("\nStarting second pass...")
            self._debug_print("Symbol table:")
            for label, addr in sorted(self.symbol_table.items(), key=lambda x: x[1]):
                self._debug_print(f"  {label}: 0x{addr:02X}")
        
        for instruction in self.intermediate:
            # Get opcode and operands safely
            opcode_str = instruction.get('opcode', '')
            operands = instruction.get('operands', [])
            operands_str = ' '.join(operands) if operands else ""
            
            # Debug info
            if self.debug:
                addr_str = f"0x{instruction.get('address', 0):02X}"
                binary_offset_str = f"0x{binary_offset:02X}"
                self._debug_print(f"\nAssembling instruction at {addr_str}: {opcode_str} {operands_str}")
                self._debug_print(f"Binary offset at {binary_offset_str}")
            
            # Store the current binary offset before assembling
            instruction['actual_binary_offset'] = binary_offset
            
            # Assemble the instruction
            binary_instruction = self._assemble_instruction(instruction)
            
            # Print the actual mapping in output binary
            if self.debug:
                binary_hex = ' '.join([f'0x{b:02X}' for b in binary_instruction])
                self._debug_print(f"{binary_offset_str}: {binary_hex} | {opcode_str} {operands_str}")
            
            # Add to binary output and update offset
            self.binary.extend(binary_instruction)
            binary_offset += len(binary_instruction)
        
        # Debug: print final symbol references
        if self.debug:
            self._debug_print("\nSymbol References:")
            for ref in self.symbol_references:
                self._debug_print(f"    Symbol reference: {ref['name']} -> 0x{ref['resolved_to']:02X} (at offset +{ref['addr'] - (ref['addr'] - 1)})")
    
    def assemble(self, assembly_code):
        """
        Assemble SimpleProc-8 assembly code into binary.
        
        Args:
            assembly_code (str): The assembly code to assemble.
            
        Returns:
            list: The assembled binary code as a list of bytes.
        """
        try:
            if self.debug:
                print("\n===== ASSEMBLY PROCESS STARTED =====")
            
            self._first_pass(assembly_code)
            self._second_pass()
            
            if self.debug:
                print("\n===== ASSEMBLY PROCESS COMPLETED =====")
                
            return self.binary
        except Exception as e:
            print(f"ERROR: Assembly failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def format_binary(self, binary=None, format_type='hex'):
        """
        Format the binary code for output.
        
        Args:
            binary (list, optional): The binary code to format. Defaults to self.binary.
            format_type (str): The output format ('hex', 'bin', 'dec', 'c_array').
            
        Returns:
            str: The formatted binary code.
        """
        if binary is None:
            binary = self.binary
            
        if format_type == 'hex':
            return ' '.join([f"0x{byte:02X}" for byte in binary])
        elif format_type == 'bin':
            return ' '.join([f"0b{byte:08b}" for byte in binary])
        elif format_type == 'dec':
            return ' '.join([str(byte) for byte in binary])
        elif format_type == 'c_array':
            return '{' + ', '.join([f"0x{byte:02X}" for byte in binary]) + '}'
        else:
            return str(binary)
    
    def get_symbol_table(self):
        """Get the current symbol table."""
        return {label: f"0x{addr:02X}" for label, addr in self.symbol_table.items()}
    
    def save_binary(self, filename):
        """
        Save the binary output to a file.
        
        Args:
            filename (str): The name of the file to save the binary to.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with open(filename, 'wb') as f:
                f.write(bytes(self.binary))
            return True
        except Exception as e:
            print(f"Error saving binary file: {str(e)}")
            return False
    
    def save_symbol_map(self, filename):
        """
        Save the symbol map to a file.
        
        Args:
            filename (str): The name of the file to save the symbol map to.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with open(filename, 'w') as f:
                f.write("# SimpleProc-8 Symbol Map\n")
                f.write("# Format: LABEL ADDRESS\n\n")
                
                for label, addr in sorted(self.symbol_table.items(), key=lambda x: x[1]):
                    f.write(f"{label} 0x{addr:02X}\n")
                    
            return True
        except Exception as e:
            print(f"Error saving symbol map: {str(e)}")
            return False
    
    def generate_debug_info(self):
        """
        Generate detailed debug information about the assembly process.
        
        Returns:
            dict: Debug information.
        """
        debug_info = {
            'binary_size': len(self.binary),
            'symbol_count': len(self.symbol_table),
            'instruction_count': len(self.intermediate),
            'symbol_references': self.symbol_references,
            'disassembly': []
        }
        
        # Generate a disassembly
        binary_offset = 0
        for instruction in self.intermediate:
            bin_instr = self._assemble_instruction(instruction)
            
            # Get info safely
            opcode = instruction.get('opcode', '')
            operands = instruction.get('operands', [])
            operands_str = ' '.join(operands) if operands else ""
            source = instruction.get('source', f"{opcode} {operands_str}")
            line_num = instruction.get('line_num', 0)
            
            for i, byte in enumerate(bin_instr):
                if i == 0:
                    debug_info['disassembly'].append({
                        'address': f"0x{binary_offset:02X}",
                        'bytes': f"0x{byte:02X}",
                        'instruction': source,
                        'line': line_num
                    })
                else:
                    debug_info['disassembly'].append({
                        'address': f"0x{binary_offset+i:02X}",
                        'bytes': f"0x{byte:02X}",
                        'instruction': f"... (data for {opcode})",
                        'line': line_num
                    })
            
            binary_offset += len(bin_instr)
            
        return debug_info
    
    def save_debug_info(self, filename):
        """
        Save debug information to a file.
        
        Args:
            filename (str): The name of the file to save debug info to.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            debug_info = self.generate_debug_info()
            
            with open(filename, 'w') as f:
                f.write("# SimpleProc-8 Assembly Debug Information\n\n")
                
                f.write("## Binary Statistics\n")
                f.write(f"Binary size: {debug_info['binary_size']} bytes\n")
                f.write(f"Instruction count: {debug_info['instruction_count']}\n")
                f.write(f"Symbol count: {debug_info['symbol_count']}\n\n")
                
                f.write("## Symbol Table\n")
                for label, addr in sorted(self.symbol_table.items(), key=lambda x: x[1]):
                    f.write(f"{label}: 0x{self.symbol_table[label]:02X}\n")
                f.write("\n")
                
                f.write("## Symbol References\n")
                for ref in debug_info['symbol_references']:
                    f.write(f"At 0x{ref['addr']:02X}: {ref['name']} -> 0x{ref['resolved_to']:02X}\n")
                f.write("\n")
                
                f.write("## Disassembly\n")
                f.write("Address  | Byte    | Source Line | Instruction\n")
                f.write("---------|---------|-------------|------------\n")
                for entry in debug_info['disassembly']:
                    f.write(f"{entry['address']}    | {entry['bytes']}    | {entry['line']:11} | {entry['instruction']}\n")
                    
            return True
        except Exception as e:
            print(f"Error saving debug info: {str(e)}")
            return False
            
    def print_instruction_summary(self):
        """
        Print a summary of all instructions and their binary representation.
        This is useful for understanding how symbols were resolved.
        """
        print("\nInstruction Summary:")
        print("--------------------")
        
        binary_offset = 0
        for instr in self.intermediate:
            bin_instr = self._assemble_instruction(instr)
            bin_str = self.format_binary(bin_instr, 'hex')
            
            # Get source safely
            opcode = instr.get('opcode', '')
            operands = instr.get('operands', [])
            operands_str = ' '.join(operands) if operands else ""
            source = instr.get('source', f"{opcode} {operands_str}")
            
            # Print the address, binary representation, and source
            print(f"0x{binary_offset:02X}: {bin_str:12} | {source}")
            
            # Check if this instruction references a symbol
            refs = [ref for ref in self.symbol_references if ref['addr'] >= binary_offset and 
                   ref['addr'] < binary_offset + len(bin_instr)]
            
            # If it does, print the symbol details
            for ref in refs:
                print(f"    Symbol reference: {ref['name']} -> 0x{ref['resolved_to']:02X} (at offset +{ref['addr'] - binary_offset})")
                
            binary_offset += len(bin_instr)


# Main function to handle command line arguments
def main():
    import argparse

    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description="SimpleProc-8 Assembler",
        epilog="Example: python assembler.py program.asm --debug --symbol-file program.sym"
    )
    
    parser.add_argument("input_file", help="Input assembly file (.asm)")
    parser.add_argument("-o", "--output", help="Output binary file (default: input_file.zz)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-s", "--symbol-file", help="Generate a symbol table file")
    parser.add_argument("-i", "--debug-info", help="Generate detailed debug information file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose instruction encoding details")
    parser.add_argument("-f", "--format", choices=["hex", "bin", "dec", "c_array"], 
                       default="hex", help="Output format for display (default: hex)")
    
    args = parser.parse_args()
    
    # Check if the input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)
    
    # Read the assembly code from the input file
    try:
        with open(args.input_file, 'r') as f:
            assembly_code = f.read()
    except Exception as e:
        print(f"Error reading input file: {str(e)}")
        sys.exit(1)
    
    # Create the output filename
    if args.output:
        output_file = args.output
    else:
        base_name = os.path.splitext(args.input_file)[0]
        output_file = f"{base_name}.zz"
    
    print(f"Assembling {args.input_file} to {output_file}")
    if args.debug:
        print("Debug mode enabled")
    
    # Create the assembler with debug mode if requested
    assembler = SimpleProc8Assembler(debug=args.debug)
    binary = assembler.assemble(assembly_code)
    
    if not binary:
        print("Assembly failed. No output file generated.")
        sys.exit(1)
    
    # Save the binary to the output file
    if assembler.save_binary(output_file):
        print(f"Assembly successful. Binary saved to '{output_file}'")
        
        # Print the symbol table
        print("\nSymbol Table:")
        for label, addr in sorted(assembler.get_symbol_table().items(), key=lambda x: x[1]):
            print(f"  {label}: {addr}")
        
        # Print a summary of the binary
        print(f"\nGenerated {len(binary)} bytes of code.")
        output_format = args.format
        binary_str = assembler.format_binary(format_type=output_format)
        print(f"Binary ({output_format}): {binary_str[:60]}..." if len(binary_str) > 60 else binary_str)
        
        # Generate symbol file if requested
        if args.symbol_file:
            if assembler.save_symbol_map(args.symbol_file):
                print(f"Symbol map saved to '{args.symbol_file}'")
            else:
                print(f"Failed to save symbol map to '{args.symbol_file}'")
        
        # Generate debug information if requested
        if args.debug_info:
            if assembler.save_debug_info(args.debug_info):
                print(f"Debug information saved to '{args.debug_info}'")
            else:
                print(f"Failed to save debug information to '{args.debug_info}'")
        
        # Print detailed instruction summary if verbose mode
        if args.verbose:
            assembler.print_instruction_summary()
            
    else:
        print(f"Failed to save binary to '{output_file}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
