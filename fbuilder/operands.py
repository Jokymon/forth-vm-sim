reg_encoding = {
    "ip": 0x0,
    "wp": 0x1,
    "rsp": 0x2,
    "dsp": 0x3,
    "acc1": 0x4,
    "acc2": 0x5,
    "pc": 0x7,
}


class RegisterOperand:
    def __init__(self, mnemonic_node, *args):
        self.mnemonic_name = str(mnemonic_node)
        self.name = self.mnemonic_name[1:]
        self.encoding = reg_encoding[self.name]
        self.line_no = mnemonic_node.line
        self.args = args
        self.is_indirect = "indirect" in self.args

    def is_(self, property):
        return property in self.args

    def __repr__(self):
        s = f"Register {self.mnemonic_name}"
        if self.is_indirect:
            s += " (indirect)"
        return s


class JumpOperand:
    def __init__(self, jump_target):
        self.jump_target = jump_target

    def __repr__(self):
        return f"Jump to {self.jump_target}"


class NumberOperand:
    def __init__(self, number):
        self.number = number