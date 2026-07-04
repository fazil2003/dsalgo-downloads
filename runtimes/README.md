# DSAlgo Compilation &amp; Execution Runtimes

This directory contains the compressed runtime and compiler libraries required to compile and execute non-JavaScript coding challenges (Python, Java, and C++) locally inside the DSAlgo application.

## Runtimes &amp; Explanations

### 1. Python Runtime (Pyodide)
* **Description**: Pyodide brings the Python runtime to the browser and WebViews via WebAssembly. It includes the CPython interpreter and packages.
* **Usage**: Used to run Python code client-side inside a secure Web Worker sandbox.
* **Original Source &amp; Download**: [Pyodide Releases](https://github.com/pyodide/pyodide/releases)

### 2. Java Runtime (TeaVM)
* **Description**: TeaVM is an ahead-of-time compiler for Java bytecode that emits JavaScript, allowing Java programs to run directly in browser and WebView environments.
* **Usage**: Transpiles Java challenge solutions into JavaScript to execute inside the sandbox.
* **Original Source &amp; Download**: [TeaVM Project](https://github.com/konsoletyper/teavm)

### 3. C++ Runtime (Emscripten / Clang)
* **Description**: Emscripten compiles C and C++ code into WebAssembly using LLVM/Clang, enabling C++ execution sandboxes inside WebViews.
* **Usage**: Compiles C++ challenge solutions to WebAssembly bytecode modules to run client-side.
* **Original Source &amp; Download**: [Emscripten Toolchain](https://github.com/emscripten-core/emsdk)
