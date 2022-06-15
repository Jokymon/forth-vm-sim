import argparse
import pathlib
from lark import Lark
from assembler import VmForthAssembler


def compile_forth(input_path, output_path, output_format):
    script_dir = pathlib.Path(__file__).parent
    lark_grammar_path = script_dir / "grammar.lark"

    grammar = lark_grammar_path.read_text()
    lark_parser = Lark(grammar, parser='lalr', transformer=VmForthAssembler())

    dictionary_source = pathlib.Path(input_path).read_text()

    if output_format == "bin":
        with open(output_path, "wb") as output_file:
            output_file.write(lark_parser.parse(dictionary_source))
    else:
        with open(output_path, "w") as output_file:
            data = lark_parser.parse(dictionary_source)
            output = ", ".join(map(hex, data))
            output_file.write(output)


def main():
    parser = argparse.ArgumentParser(description="Forth VM code compiler")
    parser.add_argument('input', metavar="INFILE", type=str,
                        help="input file for compilation")
    parser.add_argument('-o', '--output', dest='output', type=str, required=True,
                        help="output file for compiled data")
    parser.add_argument('-f', '--format', dest='format', choices=['bin', 'carray'], default="bin",
                        help="output format for the assembled code")

    args = parser.parse_args()

    compile_forth(args.input, args.output, args.format)


if __name__=="__main__":
    main()
