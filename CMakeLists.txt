cmake_minimum_required(VERSION 3.23.1)
include(cmake/CPM.cmake)
CPMAddPackage("gh:catchorg/Catch2@3.0.1")


project(forth-vm-sim)

add_library(vm)
target_include_directories(vm
    INTERFACE
        src
)
target_sources(vm
    PUBLIC
        src/vm.h
    PRIVATE
        src/vm.cpp
)

add_executable(${PROJECT_NAME})
target_sources(${PROJECT_NAME}
    PRIVATE
        src/main.cpp
)

target_link_libraries(forth-vm-sim vm -static-libgcc -static-libstdc++)

add_executable(test)
target_sources(test
    PRIVATE
        test/test_vm.cpp
)
target_link_libraries(test vm Catch2 Catch2WithMain)