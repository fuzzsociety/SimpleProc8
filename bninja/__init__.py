"""
SimpleProc8 Architecture Plugin for Binary Ninja
-----------------------------------------------
This plugin adds support for the SimpleProc-8 processor architecture
with 4 registers, 256 bytes of memory, and a simple instruction set.
"""

from binaryninja import *
import struct
import os
import sys

# Log info for debugging
log_info("Loading SimpleProc8 plugin...")

class SimpleProc8(Architecture):
    name = "SimpleProc8"
    address_size = 1  # 8-bit addresses (256 bytes of memory)
    default_int_size = 1  # 8-bit registers and operations
    max_instr_length = 2  # Maximum instruction length is 2 bytes
    
    # Define the registers for this architecture
    regs = {
        "a": RegisterInfo("a", 1),
        "b": RegisterInfo("b", 1),
        "c": RegisterInfo("c", 1),
        "d": RegisterInfo("d", 1),
        "pc": RegisterInfo("pc", 1),
        "z_flag": RegisterInfo("z_flag", 1),
        "c_flag": RegisterInfo("c_flag", 1),
        "n_flag": RegisterInfo("n_flag", 1),
        "v_flag": RegisterInfo("v_flag", 1)
    }
    
    # Fix the stack pointer issue by using one of the actual registers
    stack_pointer = "d"  # Using register 'd' as stack pointer (even though not really used)
    
    # Register mapping from encoding to name
    reg_map = {
        0b00: "a",
        0b01: "b",
        0b10: "c",
        0b11: "d"
    }
    
    # OpCode mapping
    opcodes = {
        0b0000: "ld",   # Load
        0b0001: "st",   # Store
        0b0010: "add",  # Add
        0b0011: "sub",  # Subtract
        0b0100: "inc",  # Increment
        0b0101: "dec",  # Decrement
        0b0110: "and",  # AND
        0b0111: "or",   # OR
        0b1000: "xor",  # XOR
        0b1001: "not",  # NOT
        0b1010: "jmp",  # Jump
        0b1011: "jz",   # Jump if zero
        0b1100: "jnz",  # Jump if not zero
        0b1101: "jc",   # Jump if carry
        0b1110: "nop",  # No operation
        0b1111: "hlt"   # Halt
    }
    
    # LD addressing modes
    ld_modes = {
        0b00: "immediate",  # Immediate value
        0b01: "direct",     # Memory address
        0b10: "indirect",   # Register indirect ([B])
        0b11: "register"    # Register to register
    }
    
    # ST addressing modes
    st_modes = {
        0b00: "direct",    # Memory address
        0b01: "indirect"   # Register indirect ([B])
    }
    
    # JMP addressing modes
    jmp_modes = {
        0b00: "direct",    # Direct address
        0b01: "indirect"   # Register indirect
    }

    # IMPORTANT: This is the REQUIRED implementation
    def get_instruction_info(self, data, addr):
        """Decode a SimpleProc8 instruction - this is the core method for instruction analysis"""
        # This method is required by Binary Ninja's API
        return self.decode_instruction(data, addr)
    
    def decode_instruction(self, data, addr):
        """Decode a SimpleProc8 instruction"""
        if len(data) == 0:
            return None
            
        instruction = InstructionInfo()
        instruction.length = 1  # Most instructions are 1 byte
        
        # Extract opcode from the first byte (upper 4 bits)
        opcode = (data[0] >> 4) & 0x0F
        
        # Extract register and mode
        reg = (data[0] >> 2) & 0x03
        mode = data[0] & 0x03
        
        # Process different opcodes
        if opcode == 0b0000:  # LD
            reg_name = self.reg_map.get(reg)
            mode_type = self.ld_modes.get(mode)
            
            if mode_type == "immediate":
                # Immediate mode requires a second byte
                if len(data) < 2:
                    return None
                instruction.length = 2
            
            elif mode_type == "direct":
                # Direct mode requires a second byte for address
                if len(data) < 2:
                    return None
                instruction.length = 2
                
            elif mode_type == "register":
                # Register-to-register mode requires a second byte
                if len(data) < 2:
                    return None
                instruction.length = 2
            
        elif opcode == 0b0001:  # ST
            mode_type = self.st_modes.get(mode)
            
            if mode_type == "direct":
                # Direct mode requires a second byte for address
                if len(data) < 2:
                    return None
                instruction.length = 2
                
        elif opcode in [0b1010, 0b1011, 0b1100, 0b1101]:  # JMP, JZ, JNZ, JC
            # Jump instructions require a target address
            if opcode == 0b1010:  # JMP
                jmp_mode = self.jmp_modes.get(mode)
                if jmp_mode == "direct":
                    if len(data) < 2:
                        return None
                    instruction.length = 2
                    target = data[1]
                    instruction.add_branch(BranchType.UnconditionalBranch, target)
                elif jmp_mode == "indirect":
                    # Register indirect jump - no additional bytes
                    instruction.add_branch(BranchType.IndirectBranch)
            else:  # JZ, JNZ, JC
                if len(data) < 2:
                    return None
                instruction.length = 2
                target = data[1]
                instruction.add_branch(BranchType.TrueBranch, target)
                instruction.add_branch(BranchType.FalseBranch, addr + 2)
        
        elif opcode == 0b1111:  # HLT
            # Halt is treated as a terminator instruction (like ret)
            instruction.add_branch(BranchType.FunctionReturn)
                
        return instruction
    
    def get_instruction_text(self, data, addr):
        """Convert instruction bytes to text representation"""
        if len(data) == 0:
            return None
        
        tokens = []
        instruction_len = 1
        
        # Extract parts of the instruction
        opcode = (data[0] >> 4) & 0x0F
        reg = (data[0] >> 2) & 0x03
        mode = data[0] & 0x03
        
        reg_name = self.reg_map.get(reg)
        opcode_name = self.opcodes.get(opcode)
        
        if not opcode_name:
            return None, 0
        
        # Add the opcode as a token
        tokens.append(InstructionTextToken(InstructionTextTokenType.InstructionToken, opcode_name))
        tokens.append(InstructionTextToken(InstructionTextTokenType.TextToken, " "))
        
        # Process different opcodes
        if opcode == 0b0000:  # LD
            mode_type = self.ld_modes.get(mode)
            
            # Add the destination register
            tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, reg_name))
            tokens.append(InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "))
            
            if mode_type == "immediate":
                # Immediate mode: LD Rx, #val
                if len(data) < 2:
                    return None, 0
                val = data[1]
                tokens.append(InstructionTextToken(InstructionTextTokenType.TextToken, "#"))
                tokens.append(InstructionTextToken(InstructionTextTokenType.IntegerToken, f"0x{val:02x}", val))
                instruction_len = 2
                
            elif mode_type == "direct":
                # Direct mode: LD Rx, [addr]
                if len(data) < 2:
                    return None, 0
                addr_val = data[1]
                tokens.append(InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, "["))
                tokens.append(InstructionTextToken(InstructionTextTokenType.PossibleAddressToken, f"0x{addr_val:02x}", addr_val))
                tokens.append(InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, "]"))
                instruction_len = 2
                
            elif mode_type == "indirect":
                # Indirect mode: LD Rx, [B]
                tokens.append(InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, "["))
                tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, "b"))
                tokens.append(InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, "]"))
                
            elif mode_type == "register":
                # Register mode: LD Rx, Ry
                if len(data) < 2:
                    return None, 0
                reg2 = data[1] & 0x03  # Extract register code from second byte
                reg2_name = self.reg_map.get(reg2)
                tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, reg2_name))
                instruction_len = 2
                
        elif opcode == 0b0001:  # ST
            mode_type = self.st_modes.get(mode)
            
            # Add the source register
            tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, reg_name))
            tokens.append(InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "))
            
            if mode_type == "direct":
                # Direct mode: ST Rx, [addr]
                if len(data) < 2:
                    return None, 0
                addr_val = data[1]
                tokens.append(InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, "["))
                tokens.append(InstructionTextToken(InstructionTextTokenType.PossibleAddressToken, f"0x{addr_val:02x}", addr_val))
                tokens.append(InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, "]"))
                instruction_len = 2
                
            elif mode_type == "indirect":
                # Indirect mode: ST Rx, [B]
                tokens.append(InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, "["))
                tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, "b"))
                tokens.append(InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, "]"))
        
        elif opcode in [0b0010, 0b0011, 0b0110, 0b0111, 0b1000]:  # ADD, SUB, AND, OR, XOR
            # Binary operations with two registers: OP Rx, Ry
            mode_reg = self.reg_map.get(mode)
            
            tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, reg_name))
            tokens.append(InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "))
            tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, mode_reg))
            
        elif opcode in [0b0100, 0b0101, 0b1001]:  # INC, DEC, NOT
            # Unary operations with one register: OP Rx
            tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, reg_name))
            
        elif opcode == 0b1010:  # JMP
            jmp_mode = self.jmp_modes.get(mode)
            
            if jmp_mode == "direct":
                # Direct jump: JMP addr
                if len(data) < 2:
                    return None, 0
                addr_val = data[1]
                tokens.append(InstructionTextToken(InstructionTextTokenType.PossibleAddressToken, f"0x{addr_val:02x}", addr_val))
                instruction_len = 2
                
            elif jmp_mode == "indirect":
                # Indirect jump: JMP [Rx]
                tokens.append(InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, "["))
                tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, reg_name))
                tokens.append(InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, "]"))
                
        elif opcode in [0b1011, 0b1100, 0b1101]:  # JZ, JNZ, JC
            # Conditional jumps: JZ addr, JNZ addr, JC addr
            if len(data) < 2:
                return None, 0
            addr_val = data[1]
            tokens.append(InstructionTextToken(InstructionTextTokenType.PossibleAddressToken, f"0x{addr_val:02x}", addr_val))
            instruction_len = 2
            
        elif opcode in [0b1110, 0b1111]:  # NOP, HLT
            # No operands
            pass
            
        else:
            # Unknown opcode
            tokens = [InstructionTextToken(InstructionTextTokenType.TextToken, f"UNKNOWN_{opcode:X}")]
            
        return tokens, instruction_len
    
    def get_instruction_low_level_il(self, data, addr, il):
        """Convert instruction to LLIL (for deeper analysis)"""
        if len(data) == 0:
            return None
            
        opcode = (data[0] >> 4) & 0x0F
        reg = (data[0] >> 2) & 0x03
        mode = data[0] & 0x03
        
        reg_name = self.reg_map.get(reg)
        opcode_name = self.opcodes.get(opcode)
        
        if not opcode_name:
            return None
            
        # For simplicity, we'll handle just a few key instructions
        # and omit flag handling in this version
        
        if opcode == 0b0000:  # LD
            mode_type = self.ld_modes.get(mode)
            
            if mode_type == "immediate":
                # LD Rx, #val
                if len(data) < 2:
                    return None
                val = data[1]
                il.append(il.set_reg(1, reg_name, il.const(1, val)))
                return 2
                
            elif mode_type == "direct":
                # LD Rx, [addr]
                if len(data) < 2:
                    return None
                addr_val = data[1]
                il.append(il.set_reg(1, reg_name, il.load(1, il.const(1, addr_val))))
                return 2
                
            elif mode_type == "indirect":
                # LD Rx, [B]
                il.append(il.set_reg(1, reg_name, il.load(1, il.reg(1, "b"))))
                return 1
                
            elif mode_type == "register":
                # LD Rx, Ry
                if len(data) < 2:
                    return None
                reg2 = data[1] & 0x03
                reg2_name = self.reg_map.get(reg2)
                il.append(il.set_reg(1, reg_name, il.reg(1, reg2_name)))
                return 2
                
        elif opcode == 0b0001:  # ST
            mode_type = self.st_modes.get(mode)
            
            if mode_type == "direct":
                # ST Rx, [addr]
                if len(data) < 2:
                    return None
                addr_val = data[1]
                il.append(il.store(1, il.const(1, addr_val), il.reg(1, reg_name)))
                return 2
                
            elif mode_type == "indirect":
                # ST Rx, [B]
                il.append(il.store(1, il.reg(1, "b"), il.reg(1, reg_name)))
                return 1
                
        elif opcode == 0b0010:  # ADD
            # ADD Rx, Ry
            mode_reg_name = self.reg_map.get(mode)
            result = il.add(1, il.reg(1, reg_name), il.reg(1, mode_reg_name))
            il.append(il.set_reg(1, reg_name, result))
            return 1
            
        elif opcode == 0b1010:  # JMP
            jmp_mode = self.jmp_modes.get(mode)
            
            if jmp_mode == "direct":
                # JMP addr
                if len(data) < 2:
                    return None
                target = data[1]
                il.append(il.jump(il.const(1, target)))
                return 2
                
            elif jmp_mode == "indirect":
                # JMP [Rx]
                il.append(il.jump(il.reg(1, reg_name)))
                return 1
                
        elif opcode == 0b1110:  # NOP
            # NOP - do nothing
            il.append(il.nop())
            return 1
            
        elif opcode == 0b1111:  # HLT
            # HLT - terminate the function
            il.append(il.no_ret())
            return 1
            
        # For other instructions, we'll just have a simple implementation
        # without proper flag support to ensure compatibility
        return 1

class SimpleProc8View(BinaryView):
    name = "SimpleProc8"
    long_name = "SimpleProc8 Binary"
    
    def __init__(self, data):
        log_info("Initializing SimpleProc8View")
        BinaryView.__init__(self, parent_view=data, file_metadata=data.file)
        self.raw = data
        
        try:
            arch = Architecture['SimpleProc8']
            self.platform = arch.standalone_platform
            log_info(f"Using SimpleProc8 architecture and platform")
        except Exception as e:
            log_error(f"Failed to get architecture: {e}")
    
    @classmethod
    def is_valid_for_data(self, data):
        """Check if this file can be parsed as a SimpleProc8 binary"""
        filename = data.file.filename
        log_info(f"Checking if file is valid SimpleProc8 binary: {filename}")
        
        # Check for .zz extension
        if filename.endswith('.zz'):
            log_info(f"File has .zz extension, recognizing as SimpleProc8 binary")
            return True
        
        return False
    
    # IMPORTANT: This is the REQUIRED implementation
    def perform_get_address_size(self):
        """Get address size - this is required by the BinaryView API"""
        return 1  # 8-bit address space (256 bytes)
    
    def init(self):
        """Initialize the view with segments and entry points"""
        try:
            # Get proper file length
            file_size = self.raw.length
            log_info(f"SimpleProc8 binary size: {file_size} bytes")
            
            # Dump first bytes of the file for debugging
            if file_size > 0:
                bytes_data = self.raw.read(0, min(16, file_size))
                bytes_str = " ".join([f"{b:02x}" for b in bytes_data])
                log_info(f"First bytes of file: {bytes_str}")
            
            # Add segments with proper semantics
            log_info(f"Adding segments for {file_size} bytes")
            
            # Code segment (0x00-0x7F)
            # This addresses the LinearSweep analyzer's request for ReadOnlyCodeSectionSemantics
            code_size = min(0x80, file_size)
            self.add_auto_segment(0, code_size, 0, code_size, 
                               SegmentFlag.SegmentReadable | SegmentFlag.SegmentExecutable)
            self.add_user_section("code", 0, code_size, SectionSemantics.ReadOnlyCodeSectionSemantics)
            
            # Data segment (0x80-0xFD) if available
            if file_size > 0x80:
                data_size = min(0x7E, file_size - 0x80)  # Up to 0xFD
                self.add_auto_segment(0x80, data_size, 0x80, data_size, 
                                   SegmentFlag.SegmentReadable | SegmentFlag.SegmentWritable)
                self.add_user_section("data", 0x80, data_size, SectionSemantics.ReadWriteDataSectionSemantics)
            
            # Special variables (0xFE-0xFF) if available
            if file_size > 0xFE:
                var_size = min(2, file_size - 0xFE)
                self.add_auto_segment(0xFE, var_size, 0xFE, var_size, 
                                   SegmentFlag.SegmentReadable | SegmentFlag.SegmentWritable)
                self.add_user_section("vars", 0xFE, var_size, SectionSemantics.ReadWriteDataSectionSemantics)
            
            # Set data types for important memory regions
            if file_size > 0xFE:
                self.define_data_var(0xFE, Type.int(1))  # Array length at 0xFE
                self.define_data_var(0xFF, Type.int(1))  # Temp storage at 0xFF
            
            # Data segment for the array (0x80-0xBF)
            if file_size > 0x80:
                array_size = min(64, file_size - 0x80)
                self.define_data_var(0x80, Type.array(Type.int(1), array_size))
            
            # Create a function at the entry point
            # This will kickstart the analysis
            self.add_entry_point(0)
            self.add_function(0)
            
            # Look for additional function entry points
            # This helps Binary Ninja's analysis identify more functions
            for addr in range(0, min(0x80, file_size)):
                # Look for potential function starts (LD instructions)
                try:
                    byte = self.read(addr, 1)[0]
                    if (byte >> 4) == 0:  # LD instruction
                        # Check if this might be a function start
                        if addr > 0:
                            prev_byte = self.read(addr-1, 1)[0]
                            # If preceded by JMP, HLT, or a conditional jump, likely a function
                            prev_op = (prev_byte >> 4) & 0x0F
                            if prev_op in [0b1010, 0b1011, 0b1100, 0b1101, 0b1111]:
                                self.add_function(addr)
                except:
                    pass
            
            # Apply automatic analysis
            if self.platform is not None:
                log_info("Starting analysis")
                self.update_analysis()
            
            log_info("SimpleProc8View initialization complete")
            return True
        except Exception as e:
            log_error(f"Error in SimpleProc8View initialization: {e}")
            import traceback
            log_error(traceback.format_exc())
            return False

# Register the architecture and view with appropriate error handling
try:
    log_info("Attempting to register SimpleProc8 architecture...")
    SimpleProc8.register()
    log_info("SimpleProc8 architecture registered successfully")
except Exception as e:
    log_error(f"Failed to register SimpleProc8 architecture: {str(e)}")

try:
    log_info("Attempting to register SimpleProc8View...")
    SimpleProc8View.register()
    log_info("SimpleProc8View registered successfully")
except Exception as e:
    log_error(f"Failed to register SimpleProc8View: {str(e)}")

log_info("SimpleProc8 plugin initialization complete")
