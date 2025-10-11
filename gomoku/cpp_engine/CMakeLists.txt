# CMakeLists.txt for Gomoku C++ Engine
cmake_minimum_required(VERSION 3.15)
project(gomoku_engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optimization flags
if(MSVC)
    add_compile_options(/O2 /GL /arch:AVX2)
    add_link_options(/LTCG)
else()
    add_compile_options(-O3 -march=native -flto)
endif()

# Build shared library
add_library(gomoku_engine SHARED
    gomoku_engine.cpp
    gomoku_engine.hpp
)

# Windows: use .def file for explicit exports
if(WIN32)
    target_sources(gomoku_engine PRIVATE gomoku_engine.def)
endif()

# Set output directory
set_target_properties(gomoku_engine PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}
)

# Windows: generate .dll
# Linux: generate .so
if(WIN32)
    set_target_properties(gomoku_engine PROPERTIES
        PREFIX ""
        SUFFIX ".dll"
    )
endif()
