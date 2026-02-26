---
description: Profile GPU kernel code for performance analysis
argument-hint: [reference-file] [solution-file] [--device device-type]
allowed-tools: Bash(*), Read(*), Glob(*)
---

# Makora Profile

Profile GPU kernel code to identify performance bottlenecks using the Makora API.

Always make sure to activate the installed Makora skill first.

## Task

You will profile GPU code using the Makora skill (`makora-plugin:makora-skill`) to get detailed kernel metrics and execution data.

### Arguments

- `$1`: Path to reference implementation file (baseline)
- `$2`: Path to solution implementation file (candidate to profile)
- `$3` (optional): Device specification (e.g., `--device "nvidia/H100"`, full list of devices in the Makora skill)

If arguments are not provided, ask the user for:
1. Reference code file path
2. Optimized code file path
3. Device type (default: nvidia/L40S)

## Instructions

- Refer to the Makora skill documentation (specifically **PROFILING.md**) for detailed profiling usage and output interpretation.

## Example Usage

```bash
# Basic usage with default device
/makora-plugin:profile reference.py solution.py

# With specific device
/makora-plugin:profile reference.py solution.py --device "nvidia/H100"

# Interactive mode (you'll be prompted)
/makora-plugin:profile
```
