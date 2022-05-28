#include "vm.h"
#include <conio.h>
#include <iostream>
#include <fstream>

enum class Opcode {
    OP_NOP = 0x0,
    OP_INPUT = 0x1,
    OP_OUTPUT = 0x2,
    OP_TERMINATE = 0xFE,
    OP_ILLEGAL = 0xFF
};

Vm::Vm() {
    memory.fill(static_cast<uint8_t>(Opcode::OP_ILLEGAL));

    // Setup the memory layout
    // +------------+------------+--------------+----------------+-------------+
    // | Dictionary | Data Stack | Return Stack | User Variables | I/O Buffers |
    // +------------+------------+--------------+----------------+-------------+
    //  16k           4k           4k             4k               4k
    //   -->                  <--           <--
    reg_rsp = (16+4+4) * 1024;
    reg_dsp = (16+4) * 1024;
}

void Vm::loadImage(const std::string &image_path) {
    std::fstream image_file;
    image_file.open(image_path, std::ios::in | std::ios::binary | std::ios::ate);
    auto filesize = image_file.tellg();
    if (filesize <= sizeof(memory)) {
        image_file.seekg(0);
        image_file.read(reinterpret_cast<char*>(memory.data()), filesize);
    }
    else {
        std::cout << "ERROR!! Couldn't loading binary with a size bigger than available memory size\n";
    }
    image_file.close();
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
            case Opcode::OP_OUTPUT:
                ch = memory[reg_dsp--];
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