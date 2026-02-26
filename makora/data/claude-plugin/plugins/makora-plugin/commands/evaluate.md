---
description: Evaluate candidate GPU code against reference implementation
argument-hint: [reference-file] [solution-file] [--device device-type]
allowed-tools: Bash(*), Read(*), Glob(*)
---

# Makora Evaluate

Evaluate candidate GPU kernel code against a reference implementation using the Makora API.

Always make sure to activate the installed Makora skill first.

## Task

You will benchmark GPU code by comparing a reference implementation against a solution version using the Makora skill (`makora-plugin:makora-skill`).

### Arguments

- `$1`: Path to reference implementation file (baseline)
- `$2`: Path to solution implementation file (candidate to test)
- `$3` (optional): Device specification (e.g., `--device "nvidia/H100"`, full list of devices in the Makora skill)

If arguments are not provided, ask the user for:
1. Reference code file path
2. Solution code file path
3. Device type (default: nvidia/L40S)

## Instructions

- Refer to the Makora skill documentation before trying to use the `evaluate` command.

## Example Usage

```bash
# Basic usage with default device
/makora-plugin:evaluate reference.py solution.py

# With specific device
/makora-plugin:evaluate reference.py solution.py --device "nvidia/H100"

# Interactive mode (you'll be prompted)
/makora-plugin:evaluate
```
