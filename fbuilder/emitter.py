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
JMPI_IP = 0x60
JMPI_WP = 0x61
JMPI_ACC1 = 0x62
JMPI_ACC2 = 0x63
JMPD = 0x64
JZ = 0x65
IFTK = 0xfe
ILLEGAL = 0xff

LABEL_MARKER = b"\xff\xaa"


class MachineCodeEmitter:
    def __init__(self):
        self.binary_code = b""

        self.labels = {}
        self.jumps = []

    def finalize(self):
        new_code = b""
        old_code = self.binary_code
        start_of_jump = old_code.find(LABEL_MARKER)
        while start_of_jump >= 0:
            new_code += old_code[:start_of_jump]
            jmp_index = struct.unpack("<H", old_code[start_of_jump+2:start_of_jump+4])[0]
            jump_target = self.jumps[jmp_index]
            new_code += struct.pack("<I", self.labels[jump_target])
            old_code = old_code[start_of_jump+4:]
            start_of_jump = old_code.find(LABEL_MARKER)
        new_code += old_code
        self.binary_code = new_code

    def get_current_code_address(self):
        return len(self.binary_code)

    def mark_label(self, label_text):
        self.labels[label_text] = len(self.binary_code)

    def emit_label_target(self, label_text):
        next_jumps_index = len(self.jumps)
        self.jumps.append(label_text)
        self.binary_code += LABEL_MARKER + struct.pack("<H", next_jumps_index)

    def emit_add(self, target_reg, source1_reg, source2_reg):
        opcode = ADDR_W
        operand1 = 0x0
        operand2 = 0x0

        operand1 |= (target_reg.encoding << 4)
        operand1 |= source1_reg.encoding
        operand2 |= source2_reg.encoding

        self.binary_code += struct.pack("BBB", opcode, operand1, operand2)

    def emit_conditional_jump(self, target):
        next_jumps_index = len(self.jumps)
        self.jumps.append(target.jump_target)
        self.binary_code += struct.pack("<B2sH", JZ, LABEL_MARKER, next_jumps_index)

    def emit_data_8(self, data):
        self.binary_code += struct.pack("B", data)

    def emit_data_32(self, data):
        if isinstance(data, JumpOperand):
            next_jumps_index = len(self.jumps)
            self.jumps.append(data.jump_target)
            self.binary_code += LABEL_MARKER + struct.pack("<H", next_jumps_index)
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
            next_jumps_index = len(self.jumps)
            self.jumps.append(source.jump_target)
            self.binary_code += struct.pack("<B2sH", MOVI_ACC1, LABEL_MARKER, next_jumps_index)
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
            next_jumps_index = len(self.jumps)
            self.jumps.append(target.jump_target)
            self.binary_code += struct.pack("<B2sH", JMPD, LABEL_MARKER, next_jumps_index)
        elif target.name == "ip":
            self.binary_code += struct.pack("B", JMPI_IP)
        elif target.name == "wp":
            self.binary_code += struct.pack("B", JMPI_WP)
        elif target.name == "acc1":
            self.binary_code += struct.pack("B", JMPI_ACC1)
        elif target.name == "acc2":
            self.binary_code += struct.pack("B", JMPI_ACC2)
