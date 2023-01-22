import pathlib
from lark import Lark
from assembler import VmForthAssembler
from emitter import MachineCodeEmitter, DisassemblyEmitter


class Assembler:
    def __init__(self, options=None):
        self.options = options

    def assemble_file(self):
        source_code = self.options.input.read_text()

        output = self.assemble_source(source_code)
        if self.options.format == "carray":
            output = ", ".join(map(hex, output))

        file_mode = "w"
        if self.options.format == "bin":
            file_mode += "b"
        with open(self.options.output, file_mode) as output_file:
            output_file.write(output)

    def assemble_source(self, source_code):
        script_dir = pathlib.Path(__file__).parent
        lark_grammar_path = script_dir / "grammar.lark"
        grammar = lark_grammar_path.read_text()
        lark_parser = Lark(grammar, parser='lalr')

        parse_tree = lark_parser.parse(source_code)

        if self.options.format == "disassembly":
            emitter = DisassemblyEmitter()
        else:
            emitter = MachineCodeEmitter()

        assembler = VmForthAssembler(emitter)
        assembler.visit(parse_tree)

        if self.options.format == "disassembly":
            return assembler.emitter.disassembly
        else:
            return assembler.emitter.binary_code


