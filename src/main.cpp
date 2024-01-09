#include "symbols.h"
#include "vm.h"
#include "vm_memory.h"
#include "ghc/filesystem.hpp"
#include "absl/strings/str_split.h"
#include <args.hxx>
#include <fmt/core.h>
#include <nlohmann/json.hpp>
#include <iostream>

int main(int argc, char* argv[])
{
    args::ArgumentParser parser("Forth VM");
    args::HelpFlag help(parser, "help", "Display this help menu", {'h', "help"});
    args::ValueFlag<std::string> binaryInput(parser, "binary", "Binary file containing byte code", {'i'});
    args::Flag debug(parser, "debug", "Start in debugging mode", {'d'});
    args::Flag trace(parser, "trace", "Print trace of instructions while running", {'t'});
    args::Flag dumpState(parser, "dump-state", "Dump the entire state of the CPU, including registers and stacks at the end of the run as one JSON line", {"dump-state"});
    try {
        parser.ParseCLI(argc, argv);
    }
    catch (const args::Help&) {
        std::cout << parser;
        return 0;
    }

    Symbols symbols;
    Memory main_memory;
    Memory data_stack;
    Memory return_stack;
    Vm vm{main_memory, data_stack, return_stack, symbols};

    ghc::filesystem::path binaryInputPath(args::get(binaryInput));
    main_memory.loadImageFromFile(args::get(binaryInput));
    binaryInputPath.replace_extension("sym");
    if (ghc::filesystem::exists(binaryInputPath)) {
        symbols.loadFromFile(binaryInputPath.string());
    }

    if (debug) {
        std::string input;
        Vm::Result result;
        Vm::State state;

        do {
            state = vm.getState();
            fmt::print("Pc: {:>12x}  | Dsp: {:>12x}\n",
                state.registers[Vm::Pc],
                state.registers[Vm::Dsp]);
            fmt::print("Ip: {:>12x}  | Rsp: {:>12x}\n",
                state.registers[Vm::Ip],
                state.registers[Vm::Rsp]);
            fmt::print("Wp: {:>12x}  | Acc1: {:>11x}\n",
                state.registers[Vm::Wp],
                state.registers[Vm::Acc1]);
            fmt::print("Ret: {:>12x} | Acc2: {:>11x}\n",
                state.registers[Vm::Acc2]);
            std::cout << "----------------------\n";
            auto wp_symbols = symbols.symbolsAtAddress(state.registers[Vm::Wp]);
            auto ip_symbols = symbols.symbolsAtAddress(state.registers[Vm::Ip]);
            std::cout << "Wp scopes: ";
            for (const auto &symbol: wp_symbols) {
                std::cout << symbol << ", ";
            }
            std::cout << "\n";
            std::cout << "Ip scopes: ";
            for (const auto &symbol: ip_symbols) {
                std::cout << symbol << ", ";
            }
            std::cout << "\n";
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
                    fmt::print("{:>3x}", main_memory[start_address+i]);
                    if (i%16==15) {
                        fmt::print("\n");
                        line_no++;
                    }
                }
            }

        } while ((input!="quit") && (input!="q"));
    } else {
        try {
            auto res = vm.interpret(trace);

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
        catch (memory_access_error& e) {
            fmt::print("Memory access error during interpretation; accessing {:#x} which is beyond {:#x}\n",
                       e.access_address, e.maximum_address);
        }

        if (dumpState) {
            auto vmState = vm.getState();
            nlohmann::json stateDump;
            stateDump["registers"] = {
                {"ip", vmState.registers[Vm::Ip]},
                {"wp", vmState.registers[Vm::Wp]},
                {"rsp", vmState.registers[Vm::Rsp]},
                {"dsp", vmState.registers[Vm::Dsp]},
                {"acc1", vmState.registers[Vm::Acc1]},
                {"acc2", vmState.registers[Vm::Acc2]},
                {"ret", vmState.registers[Vm::Ret]},
                {"pc", vmState.registers[Vm::Pc]},
            };
            std::vector<int> dataStack;
            for (int i=0; i<vmState.registers[Vm::Dsp]; i+=4) {
                dataStack.push_back(data_stack.get32(i));
            }
            stateDump["dataStack"] = dataStack;

            std::vector<int> returnStack;
            for (int i=0; i<vmState.registers[Vm::Rsp]; i+=4) {
                returnStack.push_back(return_stack.get32(i));
            }
            stateDump["returnStack"] = returnStack;

            std::cout << stateDump.dump() << std::endl;
        }
    }

    return 0;
}
