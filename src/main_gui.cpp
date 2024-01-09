#define SDL_MAIN_HANDLED
#include <SDL.h>
#include <imgui.h>
#include <imgui_impl_sdl.h>
#include <imgui_impl_sdlrenderer.h>
#include <ImGuiFileDialog.h>
#include <iostream>
#include "fmt/core.h"
#include "vm.h"
#include "vm_memory.h"
#include "symbols.h"

int main(int argc, char *argv[]) {
    Memory main_memory;
    Memory data_stack;
    Memory return_stack;
    Symbols symbols;
    Vm vm{main_memory, data_stack, return_stack, symbols};

    uint32_t dsp_top = 0x0;
    uint32_t rsp_bottom = 0x0;
    int current_item;

    SDL_Window *window = nullptr;

    SDL_Init(SDL_INIT_VIDEO);
    window = SDL_CreateWindow("Forth VM simulation", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 1024, 768, SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE);
    SDL_Renderer *renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_PRESENTVSYNC | SDL_RENDERER_ACCELERATED);

    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO(); (void)io;
    io.FontGlobalScale = 2.0;

    ImGui::StyleColorsDark();

    ImGui_ImplSDL2_InitForSDLRenderer(window, renderer);
    ImGui_ImplSDLRenderer_Init(renderer);

    bool isRunning = true;
    SDL_Event ev;

    while (isRunning) {
        while (SDL_PollEvent(&ev) != 0) {
            ImGui_ImplSDL2_ProcessEvent(&ev);

            if (ev.type == SDL_QUIT)
                isRunning = false;
        }

        auto registers = vm.getState();

        ImGui_ImplSDLRenderer_NewFrame();
        ImGui_ImplSDL2_NewFrame();
        ImGui::NewFrame();

        // Full screen window
        ImGui::SetNextWindowPos(ImVec2(0.0f, 0.0f));
        ImGui::SetNextWindowSize(ImGui::GetIO().DisplaySize);
        ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 0.0f);

        ImGui::Begin("Simulator", nullptr, ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoResize | ImGuiWindowFlags_MenuBar);

        if (ImGui::BeginMenuBar())
        {
            if (ImGui::BeginMenu("File"))
            {
                if (ImGui::MenuItem("Open...", "Ctrl+O"))
                {
                    ImGuiFileDialog::Instance()->OpenDialog("ChooseFileDlgKey", "Choose VM image", ".bin", ".");
                }

                ImGui::EndMenu();
            }

            ImGui::EndMenuBar();
        }

        if (ImGuiFileDialog::Instance()->Display("ChooseFileDlgKey"))
        {
            if (ImGuiFileDialog::Instance()->IsOk())
            {
                std::string filePathName = ImGuiFileDialog::Instance()->GetFilePathName();
                main_memory.loadImageFromFile(filePathName);
            }

            ImGuiFileDialog::Instance()->Close();
        }

        if (ImGui::Button("Single Step")) {
            vm.singleStep();
        }

        ImGui::Text("Next instruction: %s", vm.disassembleAtPc().c_str());

        {
            ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
            ImGui::BeginChild("Console", ImVec2(ImGui::GetContentRegionAvail().x * 0.6,
                                                ImGui::GetContentRegionAvail().y),
                            true, ImGuiWindowFlags_MenuBar);
            //ImGui::Text("Content of this child window");
            ImGui::EndChild();
            ImGui::PopStyleVar();
        }

        ImGui::SameLine();

        {
            ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
            ImGui::BeginChild("Stacks", ImVec2(ImGui::GetContentRegionAvail().x * 0.5,
                                                ImGui::GetContentRegionAvail().y),
                            true, ImGuiWindowFlags_MenuBar);

            ImGui::Text("Data Stack");
            if (ImGui::BeginListBox("Data stack", ImVec2(ImGui::GetContentRegionAvail().x,
                                                         ImGui::GetContentRegionAvail().y * 0.5))) {
                for (uint32_t address=0; address<registers.registers[Vm::Dsp]; address+=4) {
                    std::string entry_text = fmt::format("{:>8x}", data_stack.get32(address));
                    ImGui::Selectable(entry_text.c_str(), false);
                }
                ImGui::EndListBox();
            };

            ImGui::Text("Return Stack");
            if (ImGui::BeginListBox("Return stack", ImVec2(ImGui::GetContentRegionAvail().x,
                                                         ImGui::GetContentRegionAvail().y))) {
                for (uint32_t address=0; address<registers.registers[Vm::Rsp]; address+=4) {
                    std::string entry_text = fmt::format("{:>8x}", return_stack.get32(address));
                    ImGui::Selectable(entry_text.c_str(), false);
                }
                ImGui::EndListBox();
            };

            ImGui::EndChild();
            ImGui::PopStyleVar();
        }

        ImGui::SameLine();

        {
            ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
            ImGui::BeginChild("Registers", ImVec2(ImGui::GetContentRegionAvail().x,
                                                  ImGui::GetContentRegionAvail().y * 0.6),
                            true, ImGuiWindowFlags_MenuBar);

            ImGui::BeginTable("register_values", 2, ImGuiTableFlags_Borders | ImGuiTableFlags_RowBg);

            ImGui::TableSetupColumn("Name");
            ImGui::TableSetupColumn("Value");
            ImGui::TableHeadersRow();

            ImGui::TableNextColumn(); ImGui::Text("Ip"); ImGui::TableNextColumn(); ImGui::Text("%08x", registers.registers[Vm::Ip]);
            ImGui::TableNextColumn(); ImGui::Text("Wp"); ImGui::TableNextColumn(); ImGui::Text("%08x", registers.registers[Vm::Wp]);
            ImGui::TableNextColumn(); ImGui::Text("Rsp"); ImGui::TableNextColumn(); ImGui::Text("%08x", registers.registers[Vm::Rsp]);
            ImGui::TableNextColumn(); ImGui::Text("Dsp"); ImGui::TableNextColumn(); ImGui::Text("%08x", registers.registers[Vm::Dsp]);
            ImGui::TableNextColumn(); ImGui::Text("Acc1"); ImGui::TableNextColumn(); ImGui::Text("%08x", registers.registers[Vm::Acc1]);
            ImGui::TableNextColumn(); ImGui::Text("Acc2"); ImGui::TableNextColumn(); ImGui::Text("%08x", registers.registers[Vm::Acc2]);
            ImGui::TableNextColumn(); ImGui::Text("Ret"); ImGui::TableNextColumn(); ImGui::Text("%08x", registers.registers[Vm::Ret]);
            ImGui::TableNextColumn(); ImGui::Text("Pc"); ImGui::TableNextColumn(); ImGui::Text("%08x", registers.registers[Vm::Pc]);
            ImGui::EndTable();

            //ImGui::Text("Registers");
            ImGui::EndChild();
            ImGui::PopStyleVar();
        }

        ImGui::End();

        ImGui::PopStyleVar();

        // Render the frame
        ImGui::Render();
        SDL_RenderClear(renderer);
        ImGui_ImplSDLRenderer_RenderDrawData(ImGui::GetDrawData());
        SDL_RenderPresent(renderer);
    }

    ImGui_ImplSDLRenderer_Shutdown();
    ImGui_ImplSDL2_Shutdown();
    ImGui::DestroyContext();

    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();

    return 0;
}