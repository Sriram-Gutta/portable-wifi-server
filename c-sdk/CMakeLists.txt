# Generated Cmake Pico project file

cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Initialise pico_sdk from installed location
# (note this can come from environment, CMake cache etc)

# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.2.0)
set(toolchainVersion 14_2_Rel1)
set(picotoolVersion 2.2.0-a4)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================
set(PICO_BOARD pico_w CACHE STRING "Board type")

# Pull in Raspberry Pi Pico SDK (must be before project)
include(pico_sdk_import.cmake)

project(Portable_Wifi_Server C CXX ASM)

# Initialise the Raspberry Pi Pico SDK
pico_sdk_init()

# Add executable. Default name is the project name, version 0.1

add_executable(Portable_Wifi_Server Portable_Wifi_Server.c)

pico_set_program_name(Portable_Wifi_Server "Portable_Wifi_Server")
pico_set_program_version(Portable_Wifi_Server "0.1")

# Enable output over USB
pico_enable_stdio_uart(Portable_Wifi_Server 0)
pico_enable_stdio_usb(Portable_Wifi_Server 1)

# Add the standard include files to the build
target_include_directories(Portable_Wifi_Server PRIVATE
        ${CMAKE_CURRENT_LIST_DIR}
)

# Add required libraries
target_link_libraries(Portable_Wifi_Server
        pico_stdlib
        pico_cyw43_arch_lwip_poll
        hardware_adc
        pico_lwip_nosys
        )

pico_add_extra_outputs(Portable_Wifi_Server)

