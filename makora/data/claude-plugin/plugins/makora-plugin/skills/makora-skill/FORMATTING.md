# Problem and Solution File Formats

This guide explains the required file formats for `makora evaluate` and `makora profile`. Both problem (reference) and solution files must follow specific structures.

## Problem File Format (Reference Implementation)

The problem file defines the reference PyTorch implementation:

```python
import torch
import torch.nn as nn


class Model(nn.Module):
    """
    Description of the computation this model performs.
    """

    def __init__(self, *init_args):
        super(Model, self).__init__()
        # Store any parameters or buffers needed

    def forward(self, *args) -> torch.Tensor:
        """
        Reference implementation.
        
        Args:
            Describe input tensors and their shapes
            
        Returns:
            Output tensor description
        """
        # PyTorch reference implementation
        pass


# Define problem dimensions as module-level constants
M = 1024
N = 2048


def get_inputs():
    """Generate input tensors for benchmarking.
    
    Returns:
        List of input tensors (on CPU, will be moved to GPU automatically)
    """
    # Always specify dtype explicitly - default to float32 for full precision
    return [torch.rand(M, N, dtype=torch.float32), torch.rand(N, M, dtype=torch.float32)]


def get_init_inputs():
    """Return arguments for Model constructor.
    
    Returns:
        List of initialization arguments (empty list if none needed)
    """
    return []
```

### Key Requirements for Problem Files

1. **Class must be named `Model`** - inherits from `nn.Module`
2. **`forward()` method** - contains the reference computation
3. **`get_inputs()` function** - returns a list of input tensors for benchmarking
4. **`get_init_inputs()` function** - returns constructor arguments for `Model()`
5. **Input tensors on CPU** - the evaluation system moves them to GPU automatically
6. **Always specify dtype** - default to `torch.float32` for full precision

## Solution File Format

The solution file contains the candidate implementation you want to compare/profile.
Use language-specific format references for required structure details:
- **languages/TRITON.md**
- **languages/CUDA.md**

### Key Requirements for Solution Files

1. **Class must be named `ModelNew`** - not `Model`
2. **Constructor signature must match** - same arguments as `Model.__init__`
3. **Forward signature must match** - same arguments as `Model.forward`
4. **No unused code paths** - keep the solution focused on the tested forward path
5. **Results must match** - within approximately 1e-3 precision
6. **dtype must match problem file** - use the same precision as the problem's `get_inputs()`

## Converting from Other Formats

When converting code from other formats to the makora format:

1. **Identify the computation** - Find the core operation being tested
2. **For problem files**: Create the `Model` class and define `get_inputs()` / `get_init_inputs()`
3. **For solution files**: Create the `ModelNew` class with matching constructor/forward signatures

## Validation Checklist

Before running `makora evaluate`, verify:

### Problem File Checks

- [ ] Problem file has `Model` class
- [ ] `get_inputs()` returns correct tensor shapes
- [ ] `get_init_inputs()` returns correct constructor args

### Solution File Checks

- [ ] Solution file has `ModelNew` class
- [ ] Constructor signatures match
- [ ] Forward method signatures match
- [ ] Any tensors created in solution code are on the correct device
