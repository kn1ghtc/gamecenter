# C++ Engine Build Instructions

## Prerequisites

### Windows
- Visual Studio 2022 (or 2019) with C++ development tools
- CMake 3.15+

### Linux
- GCC 9+ or Clang 10+
- CMake 3.15+

## Build Steps

### Windows (PowerShell)

```powershell
# Navigate to cpp_engine directory
cd d:\pyproject\gamecenter\gomoku\cpp_engine

# Create build directory
mkdir build
cd build

# Configure with CMake (using Visual Studio)
cmake .. -G "Visual Studio 17 2022" -A x64

# Build Release version
cmake --build . --config Release

# Copy DLL to parent directory
copy Release\gomoku_engine.dll ..
```

### Alternative: Use MSVC directly

```powershell
# Set up MSVC environment
& "D:\vsstudio2022\VC\Auxiliary\Build\vcvars64.bat"

# Compile directly
cl /O2 /GL /std:c++17 /LD gomoku_engine.cpp /Fe:gomoku_engine.dll

# Move to parent
move gomoku_engine.dll ..
```

### Linux

```bash
cd d:/pyproject/gamecenter/gomoku/cpp_engine

mkdir build
cd build

cmake .. -DCMAKE_BUILD_TYPE=Release

make -j4

# Copy .so to parent
cp libgomoku_engine.so ..
```

## Verify Build

```python
# Test in Python
from gamecenter.gomoku.cpp_engine.cpp_ai_wrapper import CppAIEngine

engine = CppAIEngine()
print("C++ engine loaded successfully!")
```

## Optimization Flags Explained

### MSVC (Windows)
- `/O2`: Maximum speed optimization
- `/GL`: Whole program optimization
- `/arch:AVX2`: Use AVX2 SIMD instructions (if CPU supports)
- `/LTCG`: Link-time code generation

### GCC/Clang (Linux)
- `-O3`: Aggressive optimizations
- `-march=native`: Optimize for current CPU
- `-flto`: Link-time optimization

## Troubleshooting

### DLL not found
Ensure `gomoku_engine.dll` (Windows) or `libgomoku_engine.so` (Linux) is in the `cpp_engine/` directory.

### Compilation errors
Check that C++17 is supported and all required libraries are installed.

### Performance issues
Make sure you're building in **Release** mode, not Debug!

## Performance Expectations

- **Python baseline**: ~800 nps
- **C++ target**: 3000-5000 nps (4-6x improvement)
- **Actual speedup**: Depends on CPU, compiler, and optimization flags
