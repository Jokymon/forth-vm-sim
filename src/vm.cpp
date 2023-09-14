#include "vm.h"
#include "tools.h"
#include "fmt/core.h"
#include <iostream>
#include <fstream>
#include <map>
#ifdef _WIN32
#include <conio.h>
#else
#include <curses.h>
#endif

enum class Opcode {
    NOP = 0x0,

    MOVR_W = 0x20,
    MOVR_B = 0x21,
    MOVS_ID_W = 0x22,
    MOVS_ID_B = 0x23,
    MOVS_DI_W = 0x24,
    MOVS_DI_B = 0x25,
    MOVI_ACC1 = 0x26,
    MOVI_ACC2 = 0x27,

    ADDR_W = 0x30,
    SUBR_W = 0x32,
    ORR_W = 0x34,
    ANDR_W = 0x36,
    XORR_W = 0x38,
    SRA_W = 0x3C,

    JMPI_IP = 0x60,
    JMPI_WP = 0x61,
    JMPI_RSP = 0x62,
    JMPI_DSP = 0x63,
    JMPI_ACC1 = 0x64,
    JMPI_ACC2 = 0x65,
    JMPI_RET = 0x66,
    JMPI_PC = 0x67,
    JMPD_IP = 0x68,
    JMPD_WP = 0x69,
    JMPD_RSP = 0x6A,
    JMPD_DSP = 0x6B,
    JMPD_ACC1 = 0x6C,
    JMPD_ACC2 = 0x6D,
    JMPD_RET = 0x6E,
    JMPD_PC = 0x6F,
    JMPD = 0x70,
    JZ = 0x71,
    JC = 0x72,
    CALL = 0x73,

    PUSHRD_W = 0xA0,
    PUSHRD_W_IP = 0xA0,
    PUSHRD_W_WP = 0xA1,
    PUSHRD_W_RSP = 0xA2,
    PUSHRD_W_DSP = 0xA3,
    PUSHRD_W_ACC1 = 0xA4,
    PUSHRD_W_ACC2 = 0xA5,
    PUSHRD_W_RET = 0xA6,
    PUSHRD_W_PC = 0xA7,

    POPRD_W = 0xA8,
    POPRD_W_IP = 0xA8,
    POPRD_W_WP = 0xA9,
    POPRD_W_RSP = 0xAA,
    POPRD_W_DSP = 0xAB,
    POPRD_W_ACC1 = 0xAC,
    POPRD_W_ACC2 = 0xAD,
    POPRD_W_RET = 0xAE,
    POPRD_W_PC = 0xAF,

    PUSHRR_W = 0xB0,
    PUSHRR_W_IP = 0xB0,
    PUSHRR_W_WP = 0xB1,
    PUSHRR_W_RSP = 0xB2,
    PUSHRR_W_DSP = 0xB3,
    PUSHRR_W_ACC1 = 0xB4,
    PUSHRR_W_ACC2 = 0xB5,
    PUSHRR_W_RET = 0xB6,
    PUSHRR_W_PC = 0xB7,

    POPRR_W = 0xB8,
    POPRR_W_IP = 0xB8,
    POPRR_W_WP = 0xB9,
    POPRR_W_RSP = 0xBA,
    POPRR_W_DSP = 0xBB,
    POPRR_W_ACC1 = 0xBC,
    POPRR_W_ACC2 = 0xBD,
    POPRR_W_RET = 0xBE,
    POPRR_W_PC = 0xBF,

    IFKT = 0xFE,
    ILLEGAL = 0xFF
};

enum class IfktCodes {
    INPUT = 0x1,
    OUTPUT = 0x2,

    TERMINATE = 0xf0,
    DUMP = 0xf1,
    DUMP_M = 0xf2,
};

const std::map<uint8_t, std::string> register_name_mapping = {
    {Vm::Ip, "%ip"},
    {Vm::Wp, "%wp"},
    {Vm::Rsp, "%rsp"},
    {Vm::Dsp, "%dsp"},
    {Vm::Acc1, "%acc1"},
    {Vm::Acc2, "%acc2"},
    {Vm::Ret, "%ret"},
    {Vm::Pc, "%pc"}
};

Vm::Vm(Memory &memory, Memory &data_stack, Memory &return_stack)
: main_memory(memory)
, data_stack(data_stack)
, return_stack(return_stack) {
    std::fill(state.registers.begin(), state.registers.end(), 0x0);
}

Vm::Result Vm::singleStep() {
    char ch;
    uint8_t param8;
    uint16_t param16;
    uint32_t param32;

    uint32_t start_address;
    uint32_t end_address;

    uint8_t opcode = fetch_op();
    Opcode op = static_cast<Opcode>(opcode);
    switch (op) {
        case Opcode::NOP:
            break;
        case Opcode::ADDR_W:
            {
                param8 = fetch_op();
                uint8_t target = (param8 & 0x70) >> 4;
                uint8_t source1 = param8 & 0x7;

                param8 = fetch_op();
                uint8_t source2 = param8 & 0x7;

                state.carry = is_uint32_add_overflow(state.registers[source1], state.registers[source2]);
                state.registers[target] = state.registers[source1] + state.registers[source2];
            }

            break;
        case Opcode::SUBR_W:
            {
                param8 = fetch_op();
                uint8_t target = (param8 & 0x70) >> 4;
                uint8_t source1 = param8 & 0x7;

                param8 = fetch_op();
                uint8_t source2 = param8 & 0x7;

                state.carry = state.registers[source2] > state.registers[source1];
                state.registers[target] = state.registers[source1] - state.registers[source2];
            }

            break;
        case Opcode::ORR_W:
            {
                param8 = fetch_op();
                uint8_t target = (param8 & 0x70) >> 4;
                uint8_t source1 = param8 & 0x7;

                param8 = fetch_op();
                uint8_t source2 = param8 & 0x7;

                state.registers[target] = state.registers[source1] | state.registers[source2];
            }

            break;
        case Opcode::ANDR_W:
            {
                param8 = fetch_op();
                uint8_t target = (param8 & 0x70) >> 4;
                uint8_t source1 = param8 & 0x7;

                param8 = fetch_op();
                uint8_t source2 = param8 & 0x7;

                state.registers[target] = state.registers[source1] & state.registers[source2];
            }

            break;
        case Opcode::XORR_W:
            {
                param8 = fetch_op();
                uint8_t target = (param8 & 0x70) >> 4;
                uint8_t source1 = param8 & 0x7;

                param8 = fetch_op();
                uint8_t source2 = param8 & 0x7;

                state.registers[target] = state.registers[source1] ^ state.registers[source2];
            }

            break;
        case Opcode::SRA_W:
            {
                param8 = fetch_op();
                uint8_t reg = (param8 >> 5) & 0x7;
                uint8_t imm5 = param8 & 0x1f;

                state.registers[reg] = (int32_t)state.registers[reg] >> imm5;
            }
            break;
        case Opcode::MOVR_W:
            param8 = fetch_op();
            movr_w(param8);
            break;
        case Opcode::MOVR_B:
            param8 = fetch_op();
            movr_b(param8);
            break;
        case Opcode::MOVS_ID_W:
            param8 = fetch_op();
            movs_id_w(param8);
            break;
        case Opcode::MOVS_ID_B:
            param8 = fetch_op();
            movs_id_b(param8);
            break;
        case Opcode::MOVS_DI_W:
            param8 = fetch_op();
            movs_di_w(param8);
            break;
        case Opcode::MOVS_DI_B:
            param8 = fetch_op();
            movs_di_b(param8);
            break;
        case Opcode::MOVI_ACC1:
            param32 = main_memory.get32(state.registers[Pc]);
            state.registers[Pc] += 4;
            state.registers[Acc1] = param32;
            break;
        case Opcode::MOVI_ACC2:
            param32 = main_memory.get32(state.registers[Pc]);
            state.registers[Pc] += 4;
            state.registers[Acc2] = param32;
            break;
        case Opcode::JC:
            if (state.carry) {
                param32 = main_memory.get32(state.registers[Pc]);
                state.registers[Pc] = param32;
            }
            else {
                state.registers[Pc] += 4;
            }
            break;
        case Opcode::JMPI_IP:
        case Opcode::JMPI_WP:
        case Opcode::JMPI_RSP:
        case Opcode::JMPI_DSP:
        case Opcode::JMPI_ACC1:
        case Opcode::JMPI_ACC2:
        case Opcode::JMPI_RET:
        case Opcode::JMPI_PC:
            state.registers[Pc] = main_memory.get32(state.registers[opcode - static_cast<int>(Opcode::JMPI_IP)]);
            break;
        case Opcode::JMPD_IP:
        case Opcode::JMPD_WP:
        case Opcode::JMPD_RSP:
        case Opcode::JMPD_DSP:
        case Opcode::JMPD_ACC1:
        case Opcode::JMPD_ACC2:
        case Opcode::JMPD_RET:
        case Opcode::JMPD_PC:
            state.registers[Pc] = state.registers[opcode - static_cast<int>(Opcode::JMPD_IP)];
            break;
        case Opcode::JMPD:
            param32 = main_memory.get32(state.registers[Pc]);
            state.registers[Pc] = param32;
            break;
        case Opcode::JZ:
            if (state.registers[Acc1]==0) {
                param32 = main_memory.get32(state.registers[Pc]);
                state.registers[Pc] = param32;
            }
            else {
                state.registers[Pc] += 4;
            }
            break;
        case Opcode::CALL:
            param32 = main_memory.get32(state.registers[Pc]);
            state.registers[Ret] = state.registers[Pc]+4;
            state.registers[Pc] = param32;
            break;
        case Opcode::PUSHRD_W_IP:
        case Opcode::PUSHRD_W_WP:
        case Opcode::PUSHRD_W_RSP:
        case Opcode::PUSHRD_W_DSP:
        case Opcode::PUSHRD_W_ACC1:
        case Opcode::PUSHRD_W_ACC2:
        case Opcode::PUSHRD_W_RET:
        case Opcode::PUSHRD_W_PC:
            data_stack.put32(state.registers[Dsp],
                             state.registers[opcode - static_cast<int>(Opcode::PUSHRD_W)]);
            state.registers[Dsp] += 4;
            break;
        case Opcode::POPRD_W_IP:
        case Opcode::POPRD_W_WP:
        case Opcode::POPRD_W_RSP:
        case Opcode::POPRD_W_DSP:
        case Opcode::POPRD_W_ACC1:
        case Opcode::POPRD_W_ACC2:
        case Opcode::POPRD_W_RET:
        case Opcode::POPRD_W_PC:
            if (state.registers[Dsp] == 0x0) {
                return Error;
            }
            state.registers[Dsp] -= 4;
            state.registers[opcode - static_cast<int>(Opcode::POPRD_W)] =
                data_stack.get32(state.registers[Dsp]);
            break;
        case Opcode::PUSHRR_W_IP:
        case Opcode::PUSHRR_W_WP:
        case Opcode::PUSHRR_W_RSP:
        case Opcode::PUSHRR_W_DSP:
        case Opcode::PUSHRR_W_ACC1:
        case Opcode::PUSHRR_W_ACC2:
        case Opcode::PUSHRR_W_RET:
        case Opcode::PUSHRR_W_PC:
            return_stack.put32(state.registers[Rsp],
                             state.registers[opcode - static_cast<int>(Opcode::PUSHRR_W)]);
            state.registers[Rsp] += 4;
            break;
        case Opcode::POPRR_W_IP:
        case Opcode::POPRR_W_WP:
        case Opcode::POPRR_W_RSP:
        case Opcode::POPRR_W_DSP:
        case Opcode::POPRR_W_ACC1:
        case Opcode::POPRR_W_ACC2:
        case Opcode::POPRR_W_RET:
        case Opcode::POPRR_W_PC:
            if (state.registers[Rsp] == 0x0) {
                return Error;
            }
            state.registers[Rsp] -= 4;
            state.registers[opcode - static_cast<int>(Opcode::POPRR_W)] =
                return_stack.get32(state.registers[Rsp]);
            break;
        case Opcode::IFKT:
            param16 = fetch_op();
            param16 |= (fetch_op() << 8);
            switch (static_cast<IfktCodes>(param16)) {
                case IfktCodes::INPUT:
                    ch = getch();
                    if (0x3 == ch) {
                        std::cout << "Ctrl-C\n";
                        exit(0);
                    }
                    state.registers[Acc1] = ch;
                    std::cout << ch;
                    break;
                case IfktCodes::OUTPUT:
                    ch = state.registers[Acc1] & 0xff;
                    std::cout << ch;
                    break;
                case IfktCodes::TERMINATE:
                    return Finished;
                case IfktCodes::DUMP:
                    std::cout << "\nDump: " << main_memory.get32(state.registers[Dsp]) << "\n";
                    break;
                case IfktCodes::DUMP_M:
                    start_address = state.registers[Acc1];
                    end_address = state.registers[Acc2];
                    if (start_address > end_address)
                        std::swap(start_address, end_address);

                    for (auto addr=start_address; addr<end_address; addr+=4) {
                        fmt::print("{:08x}\n", main_memory.get32(addr));
                    }
                    break;
                default:
                    return IllegalInstruction;
            }
            break;
        case Opcode::ILLEGAL:
            return IllegalInstruction;
        default:
            fmt::print("Vm hit illegal instruction {:x} at address {:08x}\n", static_cast<int>(op), state.registers[Pc]-1);
            return IllegalInstruction;
    }
    return Success;
}

Vm::Result Vm::interpret(bool show_trace) {
    Result result;
    do {
        if (show_trace) {
            show_trace_at_pc();
        }
        result = singleStep();
    } while (Success == result);

    return result;
}

Vm::State Vm::getState() const {
    return state;
}

void Vm::setState(const Vm::State &new_state) {
    state = new_state;
}

std::string Vm::disassembleAtPc() const {
    uint32_t param;

    switch (static_cast<Opcode>(main_memory[state.registers[Pc]])) {
        case Opcode::NOP:
            return "nop";
        case Opcode::ADDR_W:
            {
                uint8_t param1 = main_memory[state.registers[Pc]+1];
                uint8_t param2 = main_memory[state.registers[Pc]+2];

                uint8_t target = (param1 & 0x70) >> 4;
                uint8_t source1 = param1 & 0x7;
                uint8_t source2 = param2 & 0x7;
                return fmt::format("add.w {}, {}, {}",
                    register_name_mapping.at(target),
                    register_name_mapping.at(source1),
                    register_name_mapping.at(source2)
                );
            }
        case Opcode::SUBR_W:
            {
                uint8_t param1 = main_memory[state.registers[Pc]+1];
                uint8_t param2 = main_memory[state.registers[Pc]+2];

                uint8_t target = (param1 & 0x70) >> 4;
                uint8_t source1 = param1 & 0x7;
                uint8_t source2 = param2 & 0x7;
                return fmt::format("sub.w {}, {}, {}",
                    register_name_mapping.at(target),
                    register_name_mapping.at(source1),
                    register_name_mapping.at(source2)
                );
            }
        case Opcode::ORR_W:
            {
                uint8_t param1 = main_memory[state.registers[Pc]+1];
                uint8_t param2 = main_memory[state.registers[Pc]+2];

                uint8_t target = (param1 & 0x70) >> 4;
                uint8_t source1 = param1 & 0x7;
                uint8_t source2 = param2 & 0x7;
                return fmt::format("or.w {}, {}, {}",
                    register_name_mapping.at(target),
                    register_name_mapping.at(source1),
                    register_name_mapping.at(source2)
                );
            }
        case Opcode::ANDR_W:
            {
                uint8_t param1 = main_memory[state.registers[Pc]+1];
                uint8_t param2 = main_memory[state.registers[Pc]+2];

                uint8_t target = (param1 & 0x70) >> 4;
                uint8_t source1 = param1 & 0x7;
                uint8_t source2 = param2 & 0x7;
                return fmt::format("and.w {}, {}, {}",
                    register_name_mapping.at(target),
                    register_name_mapping.at(source1),
                    register_name_mapping.at(source2)
                );
            }
        case Opcode::XORR_W:
            {
                uint8_t param1 = main_memory[state.registers[Pc]+1];
                uint8_t param2 = main_memory[state.registers[Pc]+2];

                uint8_t target = (param1 & 0x70) >> 4;
                uint8_t source1 = param1 & 0x7;
                uint8_t source2 = param2 & 0x7;
                return fmt::format("xor.w {}, {}, {}",
                    register_name_mapping.at(target),
                    register_name_mapping.at(source1),
                    register_name_mapping.at(source2)
                );
            }
        case Opcode::SRA_W:
            {
                uint8_t param = main_memory[state.registers[Pc]+1];
                uint8_t reg = (param >> 5) & 0x7;
                uint8_t imm5 = param & 0x1f;
                return fmt::format("sra.w {}, {:#x}",
                    register_name_mapping.at(reg),
                    imm5
                );
            }
        case Opcode::MOVR_W:
            param = main_memory[state.registers[Pc]+1];
            return fmt::format("mov.w {}", disassemble_movr_parameters(param));
        case Opcode::MOVR_B:
            param = main_memory[state.registers[Pc]+1];
            return fmt::format("mov.b {}", disassemble_movr_parameters(param));
        case Opcode::MOVS_ID_W:
            param = main_memory[state.registers[Pc]+1];
            return fmt::format("mov.w {}", disassemble_movs_parameters(param, MoveTarget::Direct));
        case Opcode::MOVS_ID_B:
            param = main_memory[state.registers[Pc]+1];
            return fmt::format("mov.b {}", disassemble_movs_parameters(param, MoveTarget::Direct));
        case Opcode::MOVS_DI_W:
            param = main_memory[state.registers[Pc]+1];
            return fmt::format("mov.w {}", disassemble_movs_parameters(param, MoveTarget::Indirect));
        case Opcode::MOVS_DI_B:
            param = main_memory[state.registers[Pc]+1];
            return fmt::format("mov.b {}", disassemble_movs_parameters(param, MoveTarget::Indirect));
        case Opcode::MOVI_ACC1:
            param = main_memory.get32(state.registers[Pc]+1);
            return fmt::format("mov %acc1, {:#x}", param);
        case Opcode::MOVI_ACC2:
            param = main_memory.get32(state.registers[Pc]+1);
            return fmt::format("mov %acc2, {:#x}", param);
        case Opcode::JC:
            param = main_memory.get32(state.registers[Pc]+1);
            return fmt::format("jc {:#x}", param);
        case Opcode::JMPI_IP:
            return "jmp [%ip]";
        case Opcode::JMPI_WP:
            return "jmp [%wp]";
        case Opcode::JMPI_RSP:
            return "jmp [%rsp]";
        case Opcode::JMPI_DSP:
            return "jmp [%dsp]";
        case Opcode::JMPI_ACC1:
            return "jmp [%acc1]";
        case Opcode::JMPI_ACC2:
            return "jmp [%acc2]";
        case Opcode::JMPI_RET:
            return "jmp [%ret]";
        case Opcode::JMPI_PC:
            return "jmp [%pc]";
        case Opcode::JMPD_IP:
            return "jmp %ip";
        case Opcode::JMPD_WP:
            return "jmp %wp";
        case Opcode::JMPD_RSP:
            return "jmp %rsp";
        case Opcode::JMPD_DSP:
            return "jmp %dsp";
        case Opcode::JMPD_ACC1:
            return "jmp %acc1";
        case Opcode::JMPD_ACC2:
            return "jmp %acc2";
        case Opcode::JMPD_RET:
            return "jmp %ret";
        case Opcode::JMPD_PC:
            return "jmp %pc";
        case Opcode::JMPD:
            param = main_memory.get32(state.registers[Pc]+1);
            return fmt::format("jmp {:#x}", param);
        case Opcode::JZ:
            param = main_memory.get32(state.registers[Pc]+1);
            return fmt::format("jz {:#x}", param);
        case Opcode::CALL:
            param = main_memory.get32(state.registers[Pc]+1);
            return fmt::format("call {:#x}", param);
        case Opcode::IFKT:
            param = main_memory.get16(state.registers[Pc]+1);
            return fmt::format("ifkt {:#x}", param);
        case Opcode::ILLEGAL:
            return "illegal";
        default:
            return fmt::format("<unknown {:x}>", main_memory[state.registers[Pc]]);
    }
}


uint8_t Vm::fetch_op() {
    return main_memory[state.registers[Pc]++];
}

void Vm::movr_b(uint8_t param) {
    uint8_t target = (param & 0x70) >> 4;
    uint8_t source = param & 0x07;

    if ((param & 0x80) && (param & 0x08)) {
        main_memory[state.registers[target]] = main_memory[state.registers[source]];
    }
    else if (param & 0x80) {
        main_memory[state.registers[target]] = state.registers[source];
    }
    else if (param & 0x08) {
        state.registers[target] = main_memory[state.registers[source]];
    }
    else {
        state.registers[target] = state.registers[source];
    }
}

void Vm::movr_w(uint8_t param) {
    uint8_t target = (param & 0x70) >> 4;
    uint8_t source = param & 0x07;

    if ((param & 0x80) && (param & 0x08)) {
        main_memory.put32(state.registers[target], main_memory.get32(state.registers[source]));
    }
    else if (param & 0x80) {
        main_memory.put32(state.registers[target], state.registers[source]);
    }
    else if (param & 0x08) {
        state.registers[target] = main_memory.get32(state.registers[source]);
    }
    else {
        state.registers[target] = state.registers[source];
    }
}

void Vm::movs_id_w(uint8_t param) {
    uint8_t target = (param & 0x38) >> 3;
    uint8_t source = param & 0x07;

    bool decrement = (param & 0x80);
    bool pre = (param & 0x40);

    if (pre) {
        if (decrement) {
            state.registers[target] -= 4;
        }
        else {
            state.registers[target] += 4;
        }
    }

    main_memory.put32(state.registers[target], state.registers[source]);

    if (!pre) {
        if (decrement) {
            state.registers[target] -= 4;
        }
        else {
            state.registers[target] += 4;
        }
    }
}

void Vm::movs_id_b(uint8_t param) {
    uint8_t target = (param & 0x38) >> 3;
    uint8_t source = param & 0x07;

    bool decrement = (param & 0x80);
    bool pre = (param & 0x40);

    if (pre) {
        if (decrement) {
            state.registers[target] -= 1;
        }
        else {
            state.registers[target] += 1;
        }
    }

    main_memory[state.registers[target]] = state.registers[source];

    if (!pre) {
        if (decrement) {
            state.registers[target] -= 1;
        }
        else {
            state.registers[target] += 1;
        }
    }
}

void Vm::movs_di_w(uint8_t param) {
    uint8_t target = (param & 0x38) >> 3;
    uint8_t source = param & 0x07;

    bool decrement = (param & 0x80);
    bool pre = (param & 0x40);

    if (pre) {
        if (decrement) {
            state.registers[source] -= 4;
        }
        else {
            state.registers[source] += 4;
        }
    }

    state.registers[target] = main_memory.get32(state.registers[source]);

    if (!pre) {
        if (decrement) {
            state.registers[source] -= 4;
        }
        else {
            state.registers[source] += 4;
        }
    }
}

void Vm::movs_di_b(uint8_t param) {
    uint8_t target = (param & 0x38) >> 3;
    uint8_t source = param & 0x07;

    bool decrement = (param & 0x80);
    bool pre = (param & 0x40);

    if (pre) {
        if (decrement) {
            state.registers[source] -= 1;
        }
        else {
            state.registers[source] += 1;
        }
    }

    state.registers[target] = main_memory[state.registers[source]];

    if (!pre) {
        if (decrement) {
            state.registers[source] -= 1;
        }
        else {
            state.registers[source] += 1;
        }
    }
}

void Vm::show_trace_at_pc() const {
    fmt::print("{:08x} {:02x} {}\n", state.registers[Pc], main_memory[state.registers[Pc]], disassembleAtPc());
}

std::string Vm::disassemble_movr_parameters(uint8_t parameter) const {
    uint8_t target = (parameter & 0x70) >> 4;
    uint8_t source = parameter & 0x07;

    if ((parameter & 0x80) && (parameter & 0x08)) {
        return fmt::format("[{}], [{}]",
            register_name_mapping.at(target),
            register_name_mapping.at(source)
            );
    }
    else if (parameter & 0x80) {
        return fmt::format("[{}], {}",
            register_name_mapping.at(target),
            register_name_mapping.at(source)
            );
    }
    else if (parameter & 0x08) {
        return fmt::format("{}, [{}]",
            register_name_mapping.at(target),
            register_name_mapping.at(source)
            );
    }
    else {
        return fmt::format("{}, {}",
            register_name_mapping.at(target),
            register_name_mapping.at(source)
            );
    }
}

std::string Vm::disassemble_movs_parameters(uint8_t parameter, MoveTarget move_target) const {
    uint8_t target = (parameter & 0x38) >> 3;
    uint8_t source = parameter & 0x07;

    bool decrement = (parameter & 0x80);
    bool pre = (parameter & 0x40);

    std::string pre_operation = decrement ? "--" : "++";
    std::string post_operation = "";
    if (!pre) {
        std::swap(pre_operation, post_operation);
    }

    if (MoveTarget::Direct == move_target) {
        return fmt::format("[{}{}{}], {}",
            pre_operation, register_name_mapping.at(target), post_operation,
            register_name_mapping.at(source)
            );
    }
    else {
        return fmt::format("{}, [{}{}{}]",
            register_name_mapping.at(target),
            pre_operation, register_name_mapping.at(source), post_operation
            );
    }
}
