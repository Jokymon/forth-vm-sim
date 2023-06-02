import pathlib
from lark import Lark
from lark.lexer import Lexer, LexerState
from assembler import VmForthAssembler
from emitter import MachineCodeEmitter, DisassemblyEmitter
from debug_symbols import WordCollection


# Recursive lexer idea copied from https://gist.github.com/MegaIng/c6abba4d9be87473d8d586734f2b39c9
# and adapted slightly
class RecursiveLexerThread:
    def __init__(self, lexer: Lexer, lexer_state: LexerState):
        self.lexer = lexer
        self.state_stack = [lexer_state]

    @classmethod
    def from_text(cls, lexer: 'Lexer', text: str):
        return cls(lexer, LexerState(text))

    def lex(self, parser_state):
        while self.state_stack:
            lexer_state = self.state_stack[-1]
            lexer = self.lexer.lex(lexer_state, parser_state)
            try:
                token = next(lexer)
            except StopIteration:
                self.state_stack.pop()  # We are done with this file
            else:
                if token.type == "_INCLUDE":
                    name = token.value.split()[-1]  # get just the string
                    name = name[1:-1]  # Remove "
                    include_file = pathlib.Path(name)
                    self.state_stack.append(LexerState(include_file.read_text()))
                yield token  # The parser still expects this token either way


class Assembler:
    def __init__(self, options=None):
        self.options = options
        self.symbols = WordCollection()

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

        if self.options.symbol_table:
            self.symbols.dump_to_file(self.options.output.with_suffix(".sym"))

    def assemble_source(self, source_code):
        script_dir = pathlib.Path(__file__).parent
        lark_grammar_path = script_dir / "grammar.lark"
        grammar = lark_grammar_path.read_text()
        lark_parser = Lark(grammar, parser='lalr', _plugins={"LexerThread": RecursiveLexerThread})

        parse_tree = lark_parser.parse(source_code)

        if self.options.format == "disassembly":
            emitter = DisassemblyEmitter()
        else:
            emitter = MachineCodeEmitter()

        self.symbols.clear()
        assembler = VmForthAssembler(emitter, self.symbols)
        assembler.visit(parse_tree)

        if self.options.format == "disassembly":
            return assembler.emitter.disassembly
        else:
            return assembler.emitter.binary_code
