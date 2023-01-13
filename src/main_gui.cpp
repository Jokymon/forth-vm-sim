#define SDL_MAIN_HANDLED
#include <SDL.h>
#include <imgui.h>
#include <imgui_impl_sdl.h>
#include <imgui_impl_sdlrenderer.h>
#include <ImGuiFileDialog.h>
#include <iostream>
#include "vm.h"

int main(int argc, char *argv[]) {
    Vm vm;

    SDL_Window *window = nullptr;

    SDL_Init(SDL_INIT_VIDEO);
    window = SDL_CreateWindow("Forth VM simulation", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 800, 600, SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE);
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

        if (ImGui::Button("Single Step")) {
            vm.singleStep();
        }

        if (ImGuiFileDialog::Instance()->Display("ChooseFileDlgKey"))
        {
            if (ImGuiFileDialog::Instance()->IsOk())
            {
                std::string filePathName = ImGuiFileDialog::Instance()->GetFilePathName();
                vm.loadImageFromFile(filePathName);
            }

            ImGuiFileDialog::Instance()->Close();
        }

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
            auto registers = vm.getState();
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