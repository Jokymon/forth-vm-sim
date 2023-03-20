#ifndef VM_H
#define VM_H

#include <array>
#include "vm_memory.h"

class Vm {
public:
    enum Result {
        Success, Finished, Error, IllegalInstruction
    };

    enum Register {
        Ip = 0x0,
        Wp = 0x1,
        Rsp = 0x2,
        Dsp = 0x3,
        Acc1 = 0x4,
        Acc2 = 0x5,
        Ret = 0x6,
        Pc = 0x7,
    };

    struct State {
        bool carry;
        std::array<uint32_t, 8> registers;
    };

    explicit Vm(Memory &memory);

    Result singleStep();
    Result interpret(bool show_trace);

    State getState() const;
    void setState(const State &new_state);

    std::string disassembleAtPc() const;

private:
    uint8_t fetch_op();

    void movr_b(uint8_t param);
    void movr_w(uint8_t param);
    void movs_id_w(uint8_t param);
    void movs_di_w(uint8_t param);

    void show_trace_at_pc() const;

    std::string disassemble_movr_parameters(uint8_t parameter) const;
    enum class MoveTarget { Direct, Indirect };
    std::string disassemble_movs_parameters(uint8_t parameter, MoveTarget move_target) const;

    State state = {
        false,
        {0, 0, 0, 0, 0, 0, 0, 0}
    };

    Memory& memory;
};

#endif