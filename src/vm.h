#ifndef VM_H
#define VM_H

#include <array>

class Vm {
public:
    enum Result {
        Success, Finished, Error, IllegalInstruction
    };

    struct State {
        uint32_t reg_ip = 0;
        uint32_t reg_wp = 0;
        uint32_t reg_rsp = 0;
        uint32_t reg_dsp = 0;
        uint32_t reg_acc1 = 0;
        uint32_t reg_acc2 = 0;
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
    uint8_t memoryAt(uint32_t address) const;

private:
    uint8_t fetch_op();

    void push_ds(uint32_t data);
    uint32_t pop_ds();

    uint32_t get32(uint32_t address);
    void put32(uint32_t address, uint32_t value);

    State state = {
        0, 0, 0, 0, 0, 0
    };

    std::array<uint8_t, 32768> memory;
};

#endif