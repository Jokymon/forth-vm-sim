#ifndef VM_H
#define VM_H

#include <array>

class Vm {
public:
    enum Result {
        Finished, Error, IllegalInstruction
    };

    Vm();

    void loadImage(const std::string &image_path);
    Result interpret();

private:
    uint8_t fetch_op();

    uint32_t reg_ip = 0;
    uint32_t reg_wp = 0;
    uint32_t reg_rsp = 0;
    uint32_t reg_dsp = 0;

    std::array<uint8_t, 32768> memory;
};

#endif