# Triton Solution Format

Use this reference for the required structure of a Triton-based solution file.

## Required Structure

1. Import `torch`, `torch.nn as nn`, `triton`, and `triton.language as tl`.
2. Define Triton kernel functions (for example, with `@triton.jit`).
3. Define a Python wrapper function that launches the kernel.
4. Define `class ModelNew(nn.Module)`.
5. Ensure `ModelNew.__init__` matches the problem file `Model.__init__` signature.
6. Ensure `ModelNew.forward` matches the problem file `Model.forward` signature.

## Minimal Layout

```python
import torch
import torch.nn as nn
import triton
import triton.language as tl


@triton.jit
def kernel(...):
    ...


def run_kernel(...):
    # Allocate outputs and launch Triton kernel(s)
    return out


class ModelNew(nn.Module):
    def __init__(self, *init_args):
        super().__init__()
        ...

    def forward(self, *args) -> torch.Tensor:
        return run_kernel(*args)
```

## Validation Notes

- Keep `ModelNew` as the entrypoint.
- Use the same dtype expectations defined by the problem file.
