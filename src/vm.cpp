#include "vm.h"
#include <conio.h>
#include <iostream>

enum class Opcode {
    OP_NOP = 0x0,
    OP_INPUT = 0x1,
    OP_TERMINATE = 0xFE,
    OP_ILLEGAL = 0xFF
};

Vm::Vm() {
    memory.fill(static_cast<uint8_t>(Opcode::OP_ILLEGAL));
    memory[0] = static_cast<uint8_t>(Opcode::OP_INPUT);

    // Setup the memory layout
    // +------------+------------+--------------+----------------+-------------+
    // | Dictionary | Data Stack | Return Stack | User Variables | I/O Buffers |
    // +------------+------------+--------------+----------------+-------------+
    //  16k           4k           4k             4k               4k
    //   -->                  <--           <--
    reg_rsp = (16+4+4) * 1024;
    reg_dsp = (16+4) * 1024;
}

Vm::Result Vm::interpret() {
    char ch;

    while (true) {
        Opcode op = static_cast<Opcode>(fetch_op());
        switch (static_cast<Opcode>(op)) {
            case Opcode::OP_INPUT:
                ch = getch();
                memory[reg_dsp--] = ch;
                std::cout << ch;
                break;
            case Opcode::OP_ILLEGAL:
                return IllegalInstruction;
            case Opcode::OP_TERMINATE:
                return Finished;
        }
    }
    return Finished;
}

uint8_t Vm::fetch_op() {
    return memory[reg_ip++];
}