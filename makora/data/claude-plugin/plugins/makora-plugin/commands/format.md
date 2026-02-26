---
description: Convert code to makora problem/solution file format
argument-hint: <input-file> [--output output-file] [--type problem|solution] [--dtype float32|float16|bfloat16]
allowed-tools: Bash(*), Read(*), Glob(*), Write(*), Edit(*)
---

# Makora Format

Convert code from other formats to the makora problem or solution file format required by `makora evaluate` and `makora profile`.

Always make sure to activate the installed Makora skill first and refer to FORMATTING.md for the required file structure.

## Usage

```bash
/makora-plugin:format <input-file> [--output <output-file>] [--type <problem|solution>] [--dtype <precision>]
```

### Arguments

- `<input-file>` (required): Path to the input file to convert
- `--output <output-file>` (optional): Path for the formatted output file
  - Defaults to `problem.py` or `solution.py` in the same directory
- `--type <problem|solution>` (optional): Output format type
  - `problem`: Create a reference implementation with `Model` class (default)
  - `solution`: Create a candidate implementation with `ModelNew` class
- `--dtype <precision>` (optional): Tensor precision for `get_inputs()`
  - `float32`: Full precision (default)
  - `float16`: Half precision
  - `bfloat16`: Brain floating point 16

### Examples

```bash
# Convert to problem format with default float32 precision
/makora-plugin:format my_kernel.py

# Convert to solution format
/makora-plugin:format candidate_kernel.py --type solution

# Specify output path
/makora-plugin:format input.py --output benchmarks/problem.py

# Use half precision
/makora-plugin:format input.py --dtype float16

# Use bfloat16 precision
/makora-plugin:format input.py --dtype bfloat16
```
