#ifndef VM_H
#define VM_H

#include <array>

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
    };

    struct State {
        std::array<uint32_t, 6> registers;
    };

    Vm();

    void loadImageFromFile(const std::string &image_path);
    template<typename Iterator>
    void loadImageFromIterator(Iterator begin, Iterator end) {
        uint32_t counter = 0;
        for (Iterator it=begin; it!=end; ++it) {
            memory[counter++] = *it;
        }
    }

    Result singleStep();
    Result interpret();

    State getState() const;
    void setState(const State &new_state);
    uint8_t byteAt(uint32_t address) const;
    uint32_t wordAt(uint32_t address) const;

private:
    uint8_t fetch_op();

    void movr_b(uint8_t param);
    void movr_w(uint8_t param);

    void push_ds(uint32_t data);
    uint32_t pop_ds();

    uint32_t get32(uint32_t address) const;
    void put32(uint32_t address, uint32_t value);

    State state = {
        0, 0, 0, 0, 0, 0
    };

    std::array<uint8_t, 32768> memory;
};

#endif