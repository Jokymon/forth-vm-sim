import argparse
import pathlib
from lark import Lark
from assembler import VmForthAssembler


def compile_forth(input_path, output_path):
    script_dir = pathlib.Path(__file__).parent
    lark_grammar_path = script_dir / "grammar.lark"

    grammar = lark_grammar_path.read_text()
    lark_parser = Lark(grammar, parser='lalr', transformer=VmForthAssembler())

    dictionary_source = pathlib.Path(input_path).read_text()

    with open(output_path, "wb") as output_file:
        output_file.write(lark_parser.parse(dictionary_source))


def main():
    parser = argparse.ArgumentParser(description="Forth VM code compiler")
    parser.add_argument('input', metavar="INFILE", type=str,
                        help="input file for compilation")
    parser.add_argument('-o', '--output', dest='output', type=str, required=True,
                        help="output file for compiled data")

    args = parser.parse_args()

    compile_forth(args.input, args.output)


if __name__=="__main__":
    main()
