#ifndef VM_MEMORY_H
#define VM_MEMORY_H

#include <array>
#include <initializer_list>
#include <string>

const static size_t MEMORY_SIZE = 32768;

class memory_access_error : public std::runtime_error {
public:
    memory_access_error(const std::string &message, uint32_t access_address,
                        uint32_t maximum_address);
    
    uint32_t access_address;
    uint32_t maximum_address;
};

class Memory {
public:
    Memory();
    Memory(std::initializer_list<uint8_t> l);

    uint8_t& operator[](size_t index);
    uint16_t get16(size_t address) const;
    uint32_t get32(size_t address) const;
    void put32(uint32_t address, uint32_t value);

    void loadImageFromFile(const std::string &image_path);
    template<typename Iterator>
    void loadImageFromIterator(Iterator begin, Iterator end) {
        uint32_t counter = 0;
        for (Iterator it=begin; it!=end; ++it) {
            memory[counter++] = *it;
        }
    }

private:
    std::array<uint8_t, MEMORY_SIZE> memory;
};

#endif