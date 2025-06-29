cmake_minimum_required(VERSION 3.10)
project(MonitorClient)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)

add_executable(monitor_client main_simple.cpp)

target_link_libraries(monitor_client 
    ws2_32
    wininet
    kernel32
    user32
    gdi32
    winspool
    shell32
    ole32
    oleaut32
    uuid
    comdlg32
    advapi32
)

if(WIN32)
    target_compile_definitions(monitor_client PRIVATE WIN32_LEAN_AND_MEAN)
    target_compile_definitions(monitor_client PRIVATE NOMINMAX)
endif()

set_target_properties(monitor_client PROPERTIES
    WIN32_EXECUTABLE TRUE
    VS_DEBUGGER_ENVIRONMENT "PATH=${CMAKE_BINARY_DIR}/$<CONFIG>"
)

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_definitions(monitor_client PRIVATE _DEBUG)
endif() 