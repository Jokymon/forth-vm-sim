cmake_minimum_required(VERSION 3.23.1)
include(cmake/CPM.cmake)



project(forth-vm-sim)

add_executable(${PROJECT_NAME})
target_sources(${PROJECT_NAME}
    PRIVATE
        src/main.cpp
        src/vm.cpp
)



target_link_libraries(forth-vm-sim -static-libgcc -static-libstdc++)


