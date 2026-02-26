---
description: Generate an updated kernel with makora expert-generate
argument-hint: <file> [--problem problem-file] [--device device-type] [--language cuda|triton] [--speedup value]
allowed-tools: Bash(*), Read(*), Glob(*)
---

# Makora Expert Generate

Run the current Makora CLI subcommand `makora expert-generate` through the plugin.

## Task

Use the Makora skill (`makora-plugin:makora-skill`) and the CLI command:

```bash
makora expert-generate <file> [options]
```

### Arguments

- `$1`: Path to the kernel file (`file`, required)
- `$2` (optional): `--problem <path>` or `-p <path>`
- `$3` (optional): `--device <device>` or `-d <device>` (default: `nvidia/L40S`)
- `$4` (optional): `--language <language>` or `-l <language>` (default: `cuda`)
- `$5` (optional): `--speedup <float>`

## Example Usage

```bash
/makora-plugin:expert-generate solution.py
/makora-plugin:expert-generate solution.py --problem problem.py --device "nvidia/H100"
/makora-plugin:expert-generate solution.py -p problem.py -d "nvidia/L40S" -l triton --speedup 0.8
```
