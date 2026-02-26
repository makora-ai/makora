# NVIDIA Device Selection

Use this guide to choose the device for evaluation and profiling runs.

## Device Names

- `nvidia/L40S` (default)
- `nvidia/H100`

## Choosing a Device

- Use `nvidia/L40S` for routine checks and day-to-day iteration.
- Use `nvidia/H100` when your target environment or acceptance criteria requires H100-specific results.
- Keep the same device across comparison runs when you need consistent, comparable numbers.

## CLI Format

```bash
--device "nvidia/L40S"
--device "nvidia/H100"
```
