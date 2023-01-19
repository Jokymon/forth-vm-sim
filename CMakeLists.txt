cmake_minimum_required(VERSION 3.16)
include(cmake/CPM.cmake)
include(cmake/imgui.cmake)
CPMAddPackage("gh:catchorg/Catch2@3.0.1")
CPMAddPackage("gh:Taywee/args#6.4.1")
CPMAddPackage("gh:fmtlib/fmt#8.1.1")
CPMAddPackage("gh:abseil/abseil-cpp#20220623.0")

project(forth-vm-sim)

add_library(vm)
target_include_directories(vm
    INTERFACE
        src
)
target_sources(vm
    PUBLIC
        src/vm.h
        src/vm_memory.h
    PRIVATE
        src/vm.cpp
        src/vm_memory.cpp
)
if(UNIX)
    target_link_libraries(vm fmt ncurses)
ELSE()
    target_link_libraries(vm fmt)
endif()

add_executable(${PROJECT_NAME})
target_sources(${PROJECT_NAME}
    PRIVATE
        src/main.cpp
)
target_link_libraries(${PROJECT_NAME} vm absl::strings args -static-libgcc -static-libstdc++)

add_executable(${PROJECT_NAME}-gui)
target_sources(${PROJECT_NAME}-gui
    PRIVATE
        src/main_gui.cpp
)
target_link_libraries(${PROJECT_NAME}-gui ImGuiFileDialog imgui vm args -static-libgcc -static-libstdc++)

add_executable(test)
target_sources(test
    PRIVATE
        test/test_vm.cpp
)
target_link_libraries(test vm Catch2 Catch2WithMain)