#include "vm_memory.h"
#include <fstream>
#include <iostream>
#include <cassert>

Memory::Memory() {}

Memory::Memory(std::initializer_list<uint8_t> l) :
    memory()
{
    // TODO: This may not properly handle a size of l that
    // is bigger than memory
    uint32_t counter = 0;
    std::copy(l.begin(), l.end(), memory.begin());
}

uint8_t& Memory::operator[](size_t index) {
    return memory[index];
}

uint16_t Memory::get16(size_t address) const {
    assert(address+1 < MEMORY_SIZE);
    return (memory[address] | (memory[address+1] << 8));
}

uint32_t Memory::get32(size_t address) const {
    assert(address+3 < MEMORY_SIZE);
    return (memory[address] | (memory[address+1] << 8) | (memory[address+2] << 16) | (memory[address+3] << 24)); 
}

void Memory::put32(uint32_t address, uint32_t value) {
    assert(address+3 < MEMORY_SIZE);
    memory[address] = value & 0xff;
    memory[address+1] = (value >> 8) & 0xff;
    memory[address+2] = (value >> 16) & 0xff;
    memory[address+3] = (value >> 24) & 0xff; 
}

void Memory::loadImageFromFile(const std::string &image_path) {
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
