# Using Makora Evaluate

The `makora evaluate` CLI command compares the performance of a candidate implementation against a reference implementation. It runs both implementations on the specified GPU device and reports execution times, speedup factor, and validation results.

## File Format Requirements

Before running evaluation, ensure your files follow the required format. You must read **FORMATTING.md** for:
- Problem file structure
- Solution file structure
- Converting code from other formats

## Command Invocation

The `makora` tool is installed as a standalone CLI command. Always invoke it directly through Bash:

```bash
makora evaluate reference.py solution.py
```

Do NOT invoke it as a Python module or a path to an executable file. The tool is installed globally and available as a system command, so it should be invoked directly as a command.

## Example Usage

```bash
# Basic usage with default device (nvidia/L40S)
makora evaluate reference.py solution.py

# Specify a different device
makora evaluate reference.py solution.py --device "nvidia/H100"
```

The output shows:
- Reference execution time (ms)
- Solution execution time (ms)
- Speedup factor (reference_time / solution_time, higher is better)
- Validation status (correctness check)
