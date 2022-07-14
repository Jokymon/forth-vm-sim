#include "vm.h"
#include "absl/strings/str_split.h"
#include <args.hxx>
#include <fmt/core.h>
#include <iostream>

int main(int argc, char* argv[])
{
    args::ArgumentParser parser("Forth VM");
    args::HelpFlag help(parser, "help", "Display this help menu", {'h', "help"});
    args::ValueFlag<std::string> binaryInput(parser, "binary", "Binary file containing byte code", {'i'});
    args::Flag debug(parser, "debug", "Start in debugging mode", {'d'});
    try {
        parser.ParseCLI(argc, argv);
    }
    catch (const args::Help&) {
        std::cout << parser;
        return 0;
    }

    Vm vm;

    vm.loadImageFromFile(args::get(binaryInput));

    if (debug) {
        std::string input;
        Vm::Result result;
        Vm::State state;

        do {
            state = vm.getState();
            fmt::print("Pc: {:>12x} | Dsp: {:>12x}\n",
                state.registers[Vm::Pc],
                state.registers[Vm::Dsp]);
            fmt::print("Ip: {:>12x} | Rsp: {:>12x}\n",
                state.registers[Vm::Ip],
                state.registers[Vm::Rsp]);
            fmt::print("Wp: {:>12x} | Acc1: {:>11x}\n",
                state.registers[Vm::Wp],
                state.registers[Vm::Acc1]);
            fmt::print("                 | Acc2: {:>11x}\n",
                state.registers[Vm::Acc2]);
            std::cout << "----------------------\n";
            std::cout << "Next instruction: " << vm.disassembleAtPc() << std::endl;
            std::cout << ">>> ";
            std::getline(std::cin, input);

            std::vector<std::string> parts = absl::StrSplit(input, ' ');

            if ((input=="s") || (input=="step")) {
                result = vm.singleStep();
            }
            else if ((parts[0]=="d") || (parts[0]=="dump")) {
                auto start_address = std::stoul(parts[1], nullptr, 0);

                int line_no = 0;
                for (int i=0; i<3*16; i++) {
                    if (i%16==0) {
                        fmt::print("{:>8x} |", start_address+line_no*16);                        
                    }
                    fmt::print("{:>3x}", vm.byteAt(start_address+i));
                    if (i%16==15) {
                        fmt::print("\n");
                        line_no++;
                    }
                }
            }

        } while ((input!="quit") && (input!="q"));
    } else {
        auto res = vm.interpret();

        switch (res) {
            case Vm::Error:
                std::cout << "Error during byte code interpretation\n";
                break;

            case Vm::Finished:
                std::cout << "Byte code interpretation successful\n";
                break;

            case Vm::IllegalInstruction:
                std::cout << "Interpreter hit invalid instruction\n";
                break;
        }
    }

    return 0;
}
