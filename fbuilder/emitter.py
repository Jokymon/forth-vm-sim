from operands import *
import struct

NOP = 0x00
MOVR_W = 0x20
MOVR_B = 0x21
MOVS_ID_W = 0x22    # indirect <-- direct move
MOVS_ID_B = 0x23    # CURRENTLY NOT SUPPORTED/IMPLEMENTED
MOVS_DI_W = 0x24    # direct <-- indirect move
MOVS_DI_B = 0x25    # CURRENTLY NOT SUPPORTED/IMPLEMENTED
MOVI_ACC1 = 0x26
ADDR_W = 0x30
SUBR_W = 0x32
XORR_W = 0x38
SRA_W = 0x3c
JMPI_IP = 0x60
JMPI_WP = 0x61
JMPI_ACC1 = 0x62
JMPI_ACC2 = 0x63
JMPD = 0x64
JZ = 0x65
IFTK = 0xfe
ILLEGAL = 0xff


class MachineCodeEmitter:
    def __init__(self):
        self.binary_code = b""

        self.labels = {}
        self.jumps = {}

    def finalize(self):
        code_buffer = self.binary_code

        for address, label in self.jumps.items():
            changed_code = code_buffer[:address]
            changed_code += struct.pack("<I", self.labels[label])
            changed_code += code_buffer[address+4:]

            code_buffer = changed_code

        self.binary_code = code_buffer

    def get_current_code_address(self):
        return len(self.binary_code)

    def mark_label(self, label_text):
        self.labels[label_text] = len(self.binary_code)

    def _insert_jump_marker(self, label):
        self.jumps[self.get_current_code_address()] = str(label)
        self.binary_code += struct.pack("<I", 0x0)

    def emit_label_target(self, label_text):
        self._insert_jump_marker(label_text)

    def emit_add(self, target_reg, source1_reg, source2_reg):
        opcode = ADDR_W
        operand1 = 0x0
        operand2 = 0x0

        operand1 |= (target_reg.encoding << 4)
        operand1 |= source1_reg.encoding
        operand2 |= source2_reg.encoding

        self.binary_code += struct.pack("BBB", opcode, operand1, operand2)

    def emit_sub(self, target_reg, source1_reg, source2_reg):
        opcode = SUBR_W
        operand1 = 0x0
        operand2 = 0x0

        operand1 |= (target_reg.encoding << 4)
        operand1 |= source1_reg.encoding
        operand2 |= source2_reg.encoding

        self.binary_code += struct.pack("BBB", opcode, operand1, operand2)

    def emit_xor(self, target_reg, source1_reg, source2_reg):
        opcode = XORR_W
        operand1 = 0x0
        operand2 = 0x0

        operand1 |= (target_reg.encoding << 4)
        operand1 |= source1_reg.encoding
        operand2 |= source2_reg.encoding

        self.binary_code += struct.pack("BBB", opcode, operand1, operand2)

    def emit_sra(self, reg, value):
        opcode = SRA_W
        operand = value.number & 0x1F
        operand |= reg.encoding << 5

        self.binary_code += struct.pack("BB", opcode, operand)

    def emit_conditional_jump(self, target):
        self.binary_code += struct.pack("B", JZ)
        self._insert_jump_marker(target.jump_target)

    def emit_data_8(self, data):
        self.binary_code += struct.pack("B", data)

    def emit_data_32(self, data):
        if isinstance(data, JumpOperand):
            self._insert_jump_marker(data.jump_target)
        elif isinstance(data, NumberOperand):
            self.binary_code += struct.pack("<I", data.number)
        else:
            self.binary_code += struct.pack("<I", data)

    def emit_data_string(self, data):
        self.binary_code += bytes(data, encoding="utf-8")

    def emit_ifkt(self, function_number):
        self.binary_code += struct.pack("<BH", IFTK, function_number.number)

    def emit_illegal(self):
        self.binary_code += struct.pack("B", ILLEGAL)

    def emit_mov(self, suffix, target, source):
        operand = 0x0

        if isinstance(source, JumpOperand):
            if target.name != "acc1":
                raise ValueError(f"label can only be moved to acc1 on line {target.line_no}")
            self.binary_code += struct.pack("<B", MOVI_ACC1)
            self._insert_jump_marker(source.jump_target)
        elif isinstance(source, NumberOperand):
            if target.name != "acc1":
                raise ValueError(f"immediate value can only be moved to acc1 on line {target.line_no}")
            self.binary_code += struct.pack("<BI", MOVI_ACC1, source.number)
        elif target.is_("increment") or target.is_("decrement") or \
            source.is_("increment") or source.is_("decrement"):
            if target.is_indirect:
                if source.is_indirect:
                    raise ValueError(f"only one argument can be register indirect for movs on line {target.line_no}")
                opcode = MOVS_ID_W
                if target.is_("decrement"):
                    operand |= 0x80
                if target.is_("prefix"):
                    operand |= 0x40
            else:
                opcode = MOVS_DI_W
                if source.is_("decrement"):
                    operand |= 0x80
                if source.is_("prefix"):
                    operand |= 0x40
            operand |= (target.encoding << 3)
            operand |= source.encoding
            self.binary_code += struct.pack("BB", opcode, operand)
        else:
            if suffix == "b":
                opcode = MOVR_B
            else:
                opcode = MOVR_W
            indirect_target = 0x0
            indirect_source = 0x0
            if target.is_indirect:
                indirect_target = 0x8
            if source.is_indirect:
                indirect_source = 0x8
            self.binary_code += struct.pack("BB", opcode,
                (source.encoding | indirect_source) | (target.encoding | indirect_target) << 4)

    def emit_nop(self):
        self.binary_code += struct.pack("B", NOP)

    def emit_jump(self, target):
        if isinstance(target, JumpOperand):
            self.binary_code += struct.pack("B", JMPD)
            self._insert_jump_marker(target.jump_target)
        elif target.name == "ip":
            self.binary_code += struct.pack("B", JMPI_IP)
        elif target.name == "wp":
            self.binary_code += struct.pack("B", JMPI_WP)
        elif target.name == "acc1":
            self.binary_code += struct.pack("B", JMPI_ACC1)
        elif target.name == "acc2":
            self.binary_code += struct.pack("B", JMPI_ACC2)


class DisassemblyEmitter:
    def __init__(self):
        self.disassembly = ""

        self.binary_emitter = MachineCodeEmitter()

    def finalize(self):
        self.binary_emitter.finalize()
        for label, address in self.binary_emitter.labels.items():
            assembly = struct.pack("<I", address)
            self.disassembly = self.disassembly.replace(
                f"@@@@{label}@@@@",
                " ".join(map(lambda n: f"{n:02x}", assembly))
            )

    def get_current_code_address(self):
        return self.binary_emitter.get_current_code_address()

    def mark_label(self, label):
        self.disassembly += f"    {label}:\n"
        self.binary_emitter.mark_label(label)

    def emit_add(self, target_reg, source1_reg, source2_reg):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_add(target_reg, source1_reg, source2_reg)
        new_pos = self.get_current_code_address()

        self.disassembly += f"{previous_pos:08x}: "
        new_assembly = self.binary_emitter.binary_code[previous_pos:new_pos]
        machine_code = " ".join(map(lambda n: f"{n:02x}", new_assembly))

        self.disassembly += f"{machine_code:<18} add {target_reg}, {source1_reg}, {source2_reg}\n"

    def emit_sub(self, target_reg, source1_reg, source2_reg):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_sub(target_reg, source1_reg, source2_reg)
        new_pos = self.get_current_code_address()

        self.disassembly += f"{previous_pos:08x}: "
        new_assembly = self.binary_emitter.binary_code[previous_pos:new_pos]
        machine_code = " ".join(map(lambda n: f"{n:02x}", new_assembly))

        self.disassembly += f"{machine_code:<18} sub {target_reg}, {source1_reg}, {source2_reg}\n"

    def emit_xor(self, target_reg, source1_reg, source2_reg):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_xor(target_reg, source1_reg, source2_reg)
        new_pos = self.get_current_code_address()

        self.disassembly += f"{previous_pos:08x}: "
        new_assembly = self.binary_emitter.binary_code[previous_pos:new_pos]
        machine_code = " ".join(map(lambda n: f"{n:02x}", new_assembly))

        self.disassembly += f"{machine_code:<18} xor {target_reg}, {source1_reg}, {source2_reg}\n"

    def emit_sra(self, reg, value):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_sra(reg, value)
        new_pos = self.get_current_code_address()

        self.disassembly += f"{previous_pos:08x}: "
        new_assembly = self.binary_emitter.binary_code[previous_pos:new_pos]
        machine_code = " ".join(map(lambda n: f"{n:02x}", new_assembly))

        self.disassembly += f"{machine_code:<18} sra {reg}, {value}\n"

    def emit_conditional_jump(self, target):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_conditional_jump(target)

        self.disassembly += f"{previous_pos:08x}: "
        self.disassembly += f"{JZ:2x} @@@@{target}@@@@     jz {target}\n"

    def emit_data_8(self, data):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_data_8(data)
        new_pos = self.get_current_code_address()

        self.disassembly += f"{previous_pos:08x}: "
        new_assembly = self.binary_emitter.binary_code[previous_pos:new_pos]
        machine_code = " ".join(map(lambda n: f"{n:02x}", new_assembly))

        self.disassembly += f"{machine_code:<18} db #0x{data:x}\n"

    def emit_data_32(self, data):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_data_32(data)

        self.disassembly += f"{previous_pos:08x}: "

        if isinstance(data, JumpOperand):
            self.disassembly += f"@@@@{data.jump_target}@@@@        dw {data.jump_target}\n"
        else:
            new_pos = self.get_current_code_address()
            new_assembly = self.binary_emitter.binary_code[previous_pos:new_pos]
            machine_code = " ".join(map(lambda n: f"{n:02x}", new_assembly))
            if not isinstance(data, NumberOperand):
                data = f"#{data:x}"
            self.disassembly += f"{machine_code:<18} dw {data}\n"

    def emit_data_string(self, data):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_data_string(data)
        new_pos = self.get_current_code_address()

        self.disassembly += f"{previous_pos:08x}: "
        new_assembly = self.binary_emitter.binary_code[previous_pos:new_pos]
        machine_code = " ".join(map(lambda n: f"{n:02x}", new_assembly))

        self.disassembly += f"{machine_code:<18} ds \"{data}\"\n"

    def emit_ifkt(self, function_number):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_ifkt(function_number)
        new_pos = self.get_current_code_address()

        self.disassembly += f"{previous_pos:08x}: "
        new_assembly = self.binary_emitter.binary_code[previous_pos:new_pos]
        machine_code = " ".join(map(lambda n: f"{n:02x}", new_assembly))

        self.disassembly += f"{machine_code:<18} ifkt {function_number}\n"

    def emit_illegal(self):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_illegal()
        new_pos = self.get_current_code_address()

        self.disassembly += f"{previous_pos:08x}: "
        new_assembly = self.binary_emitter.binary_code[previous_pos:new_pos]
        machine_code = " ".join(map(lambda n: f"{n:02x}", new_assembly))

        self.disassembly += f"{machine_code:<18} illegal\n"

    def emit_jump(self, target):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_jump(target)
        new_pos = self.get_current_code_address()

        self.disassembly += f"{previous_pos:08x}: "
        new_assembly = self.binary_emitter.binary_code[previous_pos:new_pos]
        machine_code = " ".join(map(lambda n: f"{n:02x}", new_assembly))

        self.disassembly += f"{machine_code:<18} jmp {target}\n"

    def emit_label_target(self, label_text):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_label_target(label_text)

        self.disassembly += f"{previous_pos:08x}: "
        self.disassembly += f"@@@@{label_text}@@@@        dw {label_text}\n"

    def emit_mov(self, suffix, target, source):
        previous_pos = self.get_current_code_address()
        self.binary_emitter.emit_mov(suffix, target, source)

        self.disassembly += f"{previous_pos:08x}: "

        if isinstance(source, JumpOperand):
            self.disassembly += f"{MOVI_ACC1:2x} @@@@{source.jump_target}@@@@     mov.w %acc1, {source.jump_target}\n"
        else:
            new_pos = self.get_current_code_address()
            new_assembly = self.binary_emitter.binary_code[previous_pos:new_pos]
            machine_code = " ".join(map(lambda n: f"{n:02x}", new_assembly))
            self.disassembly += f"{machine_code:<18} mov.{suffix} {target}, {source}\n"
