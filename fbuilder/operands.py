reg_encoding = {
    "ip": 0x0,
    "wp": 0x1,
    "rsp": 0x2,
    "dsp": 0x3,
    "acc1": 0x4,
    "acc2": 0x5,
    "ret": 0x6,
    "pc": 0x7,
}


JMP_COND_ZERO = 0x0
JMP_COND_CARRY = 0x1


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

    def __str__(self):
        if self.is_("decrement"):
            pre_operation = "--"
        elif self.is_("increment"):
            pre_operation = "++"
        else:
            pre_operation = ""
        post_operation = ""

        if self.is_("postfix"):
            pre_operation, post_operation = post_operation, pre_operation

        if self.is_indirect:
            return f"[{pre_operation}{self.mnemonic_name}{post_operation}]"
        return self.mnemonic_name

    def __repr__(self):
        s = f"Register {self.mnemonic_name}"
        if self.is_indirect:
            s += " (indirect)"
        return s


class JumpOperand:
    def __init__(self, jump_target):
        self.jump_target = jump_target

    def __str__(self):
        return self.jump_target

    def __repr__(self):
        return f"Jump to {self.jump_target}"


class NumberOperand:
    def __init__(self, number):
        self.number = number

    def __str__(self):
        return f"#0x{self.number:x}"