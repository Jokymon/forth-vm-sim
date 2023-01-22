import app
import argparse
import pathlib


def main():
    parser = argparse.ArgumentParser(description="Forth VM code compiler")
    parser.add_argument('input', metavar="INFILE", type=lambda p: pathlib.Path(p).absolute(),
                        help="input file for compilation")
    parser.add_argument('-o', '--output', dest='output', type=lambda p: pathlib.Path(p).absolute(),
                        required=True,
                        help="output file for compiled data")
    parser.add_argument('-f', '--format', dest='format', choices=['bin', 'carray', 'disassembly'], default="bin",
                        help="output format for the assembled code")
    parser.add_argument('--sym', dest='symbol_table', action='store_true', default=False,
                        help="flag to indicate whether a symbol table should be emitted in addition to the regular output")

    args = parser.parse_args()
    compiler = app.Assembler(args)
    compiler.assemble_file()


if __name__=="__main__":
    main()
