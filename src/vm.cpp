#include "vm.h"
#include "fmt/core.h"
#include <conio.h>
#include <iostream>
#include <fstream>
#include <map>

enum class Opcode {
    NOP = 0x0,

    MOVR_W = 0x20,
    MOVR_B = 0x21,
    MOVS_ID_W = 0x22,
    MOVS_ID_B = 0x23,   // NOT IMPLEMENTED
    MOVS_DI_W = 0x24,
    MOVS_DI_B = 0x25,   // NOT IMPLEMENTED
    MOVI_ACC1 = 0x26,

    ADD = 0x30,

    JMPI_IP = 0x60,
    JMPI_WP = 0x61,
    JMPI_ACC1 = 0x62,
    JMPI_ACC2 = 0x63,
    JMPD = 0x64,

    IFKT = 0xFE,
    ILLEGAL = 0xFF
};

enum class IfktCodes {
    INPUT = 0x1,
    OUTPUT = 0x2,

    TERMINATE = 0xf0,
    DUMP = 0xf1,
};

const std::map<uint8_t, std::string> register_name_mapping = {
    {Vm::Ip, "%ip"},
    {Vm::Wp, "%wp"},
    {Vm::Rsp, "%rsp"},
    {Vm::Dsp, "%dsp"},
    {Vm::Acc1, "%acc1"},
    {Vm::Acc2, "%acc2"},
    {Vm::Pc, "%pc"}
};

Vm::Vm() {
    memory.fill(static_cast<uint8_t>(Opcode::ILLEGAL));

    // Setup the memory layout
    // +------------+------------+--------------+----------------+-------------+
    // | Dictionary | Data Stack | Return Stack | User Variables | I/O Buffers |
    // +------------+------------+--------------+----------------+-------------+
    //  16k           4k           4k             4k               4k
    //   -->                  <--           <--
    state.registers[Rsp] = (16+4+4) * 1024;
    state.registers[Dsp] = (16+4) * 1024;
}

void Vm::loadImageFromFile(const std::string &image_path) {
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

Vm::Result Vm::singleStep() {
    char ch;
    uint8_t param8;
    uint16_t param16;
    uint32_t param32;

    Opcode op = static_cast<Opcode>(fetch_op());
    switch (op) {
        case Opcode::NOP:
            break;
        case Opcode::ADD:
            state.registers[Acc1] = pop_ds();
            state.registers[Acc2] = pop_ds();
            push_ds(state.registers[Acc1] + state.registers[Acc2]);
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
        case Opcode::MOVS_DI_W:
            param8 = fetch_op();
            movs_di_w(param8);
            break;
        case Opcode::MOVI_ACC1:
            param32 = get32(state.registers[Pc]);
            state.registers[Pc] += 4;
            state.registers[Acc1] = param32;
            break;
        case Opcode::JMPI_IP:
            state.registers[Pc] = get32(state.registers[Ip]);
            break;
        case Opcode::JMPI_WP:
            state.registers[Pc] = get32(state.registers[Wp]);
            break;
        case Opcode::JMPI_ACC1:
            state.registers[Pc] = get32(state.registers[Acc1]);
            break;
        case Opcode::JMPI_ACC2:
            state.registers[Pc] = get32(state.registers[Acc2]);
            break;
        case Opcode::JMPD:
            param32 = get32(state.registers[Pc]);
            state.registers[Pc] = param32;
            break;
        case Opcode::IFKT:
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
                    std::cout << "\nDump: " << get32(state.registers[Dsp]) << "\n";
                    break;
                default:
                    return IllegalInstruction;
            }
            break;
        case Opcode::ILLEGAL:
            return IllegalInstruction;
        default:
            return IllegalInstruction;
    }
    return Success;
}

Vm::Result Vm::interpret() {
    Result result;
    do {
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

uint8_t Vm::byteAt(uint32_t address) const {
    return memory[address];
}

uint32_t Vm::wordAt(uint32_t address) const {
    return get32(address);
}

std::string Vm::disassembleAtPc() const {
    uint32_t param;

    switch (static_cast<Opcode>(memory[state.registers[Pc]])) {
        case Opcode::NOP:
            return "nop";
        case Opcode::MOVR_W:
            param = memory[state.registers[Pc]+1];
            return fmt::format("mov.w {}", disassemble_movr_parameters(param));
        case Opcode::MOVR_B:
            param = memory[state.registers[Pc]+1];
            return fmt::format("mov.b {}", disassemble_movr_parameters(param));
        case Opcode::MOVS_ID_W:
            param = memory[state.registers[Pc]+1];
            return fmt::format("mov.w {}", disassemble_movs_parameters(param, MoveTarget::Direct));
        case Opcode::MOVS_DI_W:
            param = memory[state.registers[Pc]+1];
            return fmt::format("mov.w {}", disassemble_movs_parameters(param, MoveTarget::Indirect));
        case Opcode::MOVI_ACC1:
            param = get32(state.registers[Pc]+1);
            return fmt::format("mov %acc1, {:#x}", param);
        case Opcode::JMPI_IP:
            return "jmp [%ip]";
        case Opcode::JMPI_WP:
            return "jmp [%wp]";
        case Opcode::JMPI_ACC1:
            return "jmp [%acc1]";
        case Opcode::JMPI_ACC2:
            return "jmp [%acc2]";
        case Opcode::JMPD:
            param = get32(state.registers[Pc]+1);
            return fmt::format("jmp {:#x}", param);
        case Opcode::IFKT:
            param = get16(state.registers[Pc]+1);
            return fmt::format("ifkt {:#x}", param);
        case Opcode::ILLEGAL:
            return "illegal";
        default:
            return fmt::format("<unknown {:x}>", memory[state.registers[Pc]]);
    }
}


uint8_t Vm::fetch_op() {
    return memory[state.registers[Pc]++];
}

void Vm::movr_b(uint8_t param) {
    uint8_t target = (param & 0x70) >> 4;
    uint8_t source = param & 0x07;

    if ((param & 0x80) && (param & 0x08)) {
        memory[state.registers[target]] = memory[state.registers[source]];
    }
    else if (param & 0x80) {
        memory[state.registers[target]] = state.registers[source];
    }
    else if (param & 0x08) {
        state.registers[target] = memory[state.registers[source]];
    }
    else {
        state.registers[target] = state.registers[source];
    }
}

void Vm::movr_w(uint8_t param) {
    uint8_t target = (param & 0x70) >> 4;
    uint8_t source = param & 0x07;

    if ((param & 0x80) && (param & 0x08)) {
        put32(state.registers[target], get32(state.registers[source]));
    }
    else if (param & 0x80) {
        put32(state.registers[target], state.registers[source]);
    }
    else if (param & 0x08) {
        state.registers[target] = get32(state.registers[source]);
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

    put32(state.registers[target], state.registers[source]);

    if (!pre) {
        if (decrement) {
            state.registers[target] -= 4;
        }
        else {
            state.registers[target] += 4;
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

    state.registers[target] = get32(state.registers[source]);

    if (!pre) {
        if (decrement) {
            state.registers[source] -= 4;
        }
        else {
            state.registers[source] += 4;
        }
    }
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


void Vm::push_ds(uint32_t data) {
    state.registers[Dsp] -= 4;
    put32(state.registers[Dsp], data);
}

uint32_t Vm::pop_ds() {
    uint32_t value = get32(state.registers[Dsp]);
    state.registers[Dsp] += 4;
    return value;
}

uint16_t Vm::get16(uint32_t address) const {
    return (memory[address] | (memory[address+1] << 8));
}

uint32_t Vm::get32(uint32_t address) const {
    return (memory[address] | (memory[address+1] << 8) | (memory[address+2] << 16) | (memory[address+3] << 24));
}

void Vm::put32(uint32_t address, uint32_t value) {
    memory[address] = value & 0xff;
    memory[address+1] = (value >> 8) & 0xff;
    memory[address+2] = (value >> 16) & 0xff;
    memory[address+3] = (value >> 24) & 0xff;
}
