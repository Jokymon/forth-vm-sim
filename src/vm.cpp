#include "vm.h"
#include <conio.h>
#include <iostream>
#include <fstream>

enum class Opcode {
    OP_NOP = 0x0,

    OP_ADD = 0x20,

    OP_IFKT = 0xFE,
    OP_ILLEGAL = 0xFF
};

enum class IfktCodes {
    INPUT = 0x1,
    OUTPUT = 0x2,

    TERMINATE = 0xf0,
    DUMP = 0xf1,
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
    uint16_t param16;

    while (true) {
        Opcode op = static_cast<Opcode>(fetch_op());
        switch (op) {
            case Opcode::OP_NOP:
                break;
            case Opcode::OP_ADD:
                reg_acc1 = pop_ds();
                reg_acc2 = pop_ds();
                push_ds(reg_acc1 + reg_acc2);
                break;
            case Opcode::OP_IFKT:
                param16 = fetch_op();
                param16 |= (fetch_op() << 8);
                switch (static_cast<IfktCodes>(param16)) {
                    case IfktCodes::INPUT:
                        ch = getch();
                        push_ds(ch);
                        std::cout << ch;
                        break;
                    case IfktCodes::OUTPUT:
                        ch = pop_ds() & 0xff;
                        std::cout << ch;
                        break;
                    case IfktCodes::TERMINATE:
                        return Finished;
                    case IfktCodes::DUMP:
                        std::cout << "\nDump: " << get32(reg_dsp) << "\n";
                        break;
                    default:
                        return IllegalInstruction;
                }
                break;
            case Opcode::OP_ILLEGAL:
                return IllegalInstruction;
        }
    }
    return Finished;
}

uint8_t Vm::fetch_op() {
    return memory[reg_ip++];
}

void Vm::push_ds(uint32_t data) {
    reg_dsp -= 4;
    put32(reg_dsp, data);
}

uint32_t Vm::pop_ds() {
    uint32_t value = get32(reg_dsp);
    reg_dsp += 4;
    return value;
}

uint32_t Vm::get32(uint32_t address) {
    return (memory[address] | (memory[address+1] << 8) | (memory[address+2] << 16) | (memory[address+3] << 24));
}

void Vm::put32(uint32_t address, uint32_t value) {
    memory[address] = value & 0xff;
    memory[address+1] = (value >> 8) & 0xff;
    memory[address+2] = (value >> 16) & 0xff;
    memory[address+3] = (value >> 24) & 0xff;
}
