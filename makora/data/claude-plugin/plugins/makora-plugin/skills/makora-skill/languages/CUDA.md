# CUDA Solution Format

Use this reference for the required structure of a CUDA-based solution file.

## Required Structure

1. Import `torch` and `torch.nn as nn`.
2. Include CUDA kernel source and a Python launch path (for example, via a compiled extension).
3. Define a Python wrapper that launches the CUDA implementation.
4. Define `class ModelNew(nn.Module)`.
5. Ensure `ModelNew.__init__` matches the problem file `Model.__init__` signature.
6. Ensure `ModelNew.forward` matches the problem file `Model.forward` signature.

## Minimal Layout

```python
import torch
import torch.nn as nn


def run_cuda_impl(...):
    # Compile/load CUDA extension and launch kernels
    return out


class ModelNew(nn.Module):
    def __init__(self, *init_args):
        super().__init__()
        ...

    def forward(self, *args) -> torch.Tensor:
        return run_cuda_impl(*args)
```

## Validation Notes

- Keep `ModelNew` as the entrypoint.
- Use the same dtype expectations defined by the problem file.
