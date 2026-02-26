# Using Makora Expert Generate

The `makora expert-generate` CLI command updates kernel code using Makora's expert-generate endpoint.

## Command Invocation

```bash
makora expert-generate <file> [options]
```

## Options

- `file` (required): Path to the kernel file
- `--problem` or `-p`: Path to a reference/problem file
- `--device` or `-d`: Device name (default: `nvidia/L40S`)
- `--language` or `-l`: Language value (default: `cuda`)
- `--speedup`: Current speedup value for context

## Output Behavior

- Status/summary is written to stderr.
- Generated code is written to stdout.

## Examples

```bash
makora expert-generate solution.py
makora expert-generate solution.py --problem problem.py --device "nvidia/H100"
makora expert-generate solution.py -p problem.py -d "nvidia/L40S" -l triton --speedup 0.8
```
