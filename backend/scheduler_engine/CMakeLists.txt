cmake_minimum_required(VERSION 3.15)
project(scheduler_engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

execute_process(
    COMMAND python -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(scheduler_engine
    bindings.cpp
    src/scheduler.cpp
)

# Drop the compiled module one level up (backend/), next to app/, so it's
# importable as `import scheduler_engine` from anywhere in the FastAPI app
# without any sys.path or PYTHONPATH gymnastics.
set_target_properties(scheduler_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/..
)