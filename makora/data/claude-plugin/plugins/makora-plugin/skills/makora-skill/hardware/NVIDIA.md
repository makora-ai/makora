# NVIDIA Device Selection

Use this guide to choose the device for evaluation and profiling runs.

## Device Names

- `L40S` (default)
- `H100`

## Choosing a Device

- Use `L40S` for routine checks and day-to-day iteration.
- Use `H100` when your target environment or acceptance criteria requires H100-specific results.
- Keep the same device across comparison runs when you need consistent, comparable numbers.

## CLI Format

```bash
--device "L40S"
--device "H100"
```
