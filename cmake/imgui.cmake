CPMAddPackage(
    NAME SDL2
    GIT_TAG "release-2.30.11"
    GITHUB_REPOSITORY libsdl-org/SDL
    OPTIONS
        "SDL_STATIC ON"
        "SDL_SHARED OFF"
)
CPMAddPackage(
    NAME imgui
    GITHUB_REPOSITORY ocornut/imgui
    VERSION 1.87
    DOWNLOAD_ONLY YES
)

CPMAddPackage(
    NAME ImGuiFileDialog
    GITHUB_REPOSITORY aiekick/ImGuiFileDialog
    VERSION 0.6.4
    DOWNLOAD_ONLY YES
)

if (imgui_ADDED)
    add_library(imgui STATIC
        ${imgui_SOURCE_DIR}/imgui.cpp
        ${imgui_SOURCE_DIR}/imgui_draw.cpp
        ${imgui_SOURCE_DIR}/imgui_tables.cpp
        ${imgui_SOURCE_DIR}/imgui_widgets.cpp
        ${imgui_SOURCE_DIR}/backends/imgui_impl_sdl.cpp
        ${imgui_SOURCE_DIR}/backends/imgui_impl_sdlrenderer.cpp
    )

    target_include_directories(imgui
        PUBLIC
            $<BUILD_INTERFACE:${imgui_SOURCE_DIR}>
            $<BUILD_INTERFACE:${imgui_SOURCE_DIR}>/backends
    )
    target_link_libraries(imgui
        PUBLIC
            SDL2-static
    )
endif()

if (ImGuiFileDialog_ADDED)
    configure_file(${CMAKE_SOURCE_DIR}/patch/ImGuiFileDialogConfig.h ${ImGuiFileDialog_SOURCE_DIR}/ImGuiFileDialogConfig.h COPYONLY)
    add_library(ImGuiFileDialog STATIC
        ${ImGuiFileDialog_SOURCE_DIR}/ImGuiFileDialog.cpp
    )

    target_include_directories(ImGuiFileDialog
    PUBLIC
        $<BUILD_INTERFACE:${ImGuiFileDialog_SOURCE_DIR}>
    )
    target_link_libraries(ImGuiFileDialog
    PUBLIC
        imgui
    )
endif()
