# Using Makora Profile

The `makora profile` CLI command performs full profiling on Nvidia GPU kernel code. It provides detailed metrics including kernel execution times, memory usage, and low-level profiling data such as CUDA source code, SASS assembly, and Nsight Systems reports.

## Supported Devices

Currently, the profiler supports profiling on Nvidia GPUs.

## Command Invocation

The `makora` tool is installed as a standalone CLI command. Always invoke it directly through Bash:

```bash
makora profile reference.py solution.py
```

Do NOT invoke it as a Python module or a path to an executable file. The tool is available as a system command, so it should be invoked directly as a command.

## Example Usage

```bash
# Basic usage with default device (nvidia/L40S)
makora profile reference.py solution.py

# Specify a different device
makora profile reference.py solution.py --device "nvidia/H100"
```

## Profiling Output

The profiler returns detailed information for each kernel:

- **Raw Metrics**: Low-level performance counters and timing data
- **Details Page**: High-level summary of kernel performance
- **Nsys Report**: Nsight Systems profiling report with timeline data
- **CUDA Code**: Source CUDA code (when available)
- **SASS Code**: GPU assembly code (when available)
- **Torch Trace**: PyTorch execution trace (when available)

## When to Use Profiling

Use profiling when you need to:
- Identify performance bottlenecks in your kernel
- Understand memory access patterns
- Analyze kernel launch configurations
- Debug performance issues before/after code changes
- Get low-level hardware metrics

For benchmarking and comparing solution code against a reference implementation, use `makora evaluate` instead. See EVALUATION.md for details.

## Code Requirements

The code being profiled must define a `ModelNew` class as the entry point. This is the same structure used for evaluation. See FORMATTING.md for the expected file structure.
