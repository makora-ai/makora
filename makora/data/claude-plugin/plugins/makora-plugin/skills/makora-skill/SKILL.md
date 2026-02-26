---
name: makora-skill
description: Format, evaluate, and profile GPU kernel code using the Makora API
allowed-tools: Bash(*), Read(*), Glob(*)
user-invocable: true
---

# Makora GPU Kernel Skill

## When This Skill Applies

Use this skill when the user mentions:
- Evaluating or benchmarking GPU code
- Profiling GPU code
- Running expert-generate on an existing kernel file
- Searching Makora indexed documents with document-search
- Converting code into Makora file format
- Makora or the Makora API/CLI

## Important Defaults

- **Always use `torch.float32` dtype** unless the problem explicitly specifies otherwise (e.g., `torch.float16` or `torch.bfloat16`)

## Workflow

1. **ALWAYS read FORMATTING.md first** when creating or converting files - this defines the exact required structure
2. Identify reference (problem definition) and candidate (solution) implementation files
3. If files need conversion to the Makora format, follow the structure in **FORMATTING.md** exactly
4. Refer to **EVALUATION.md** for command usage and examples
5. Refer to **GPUS.md** for available devices
6. Run the evaluation command
7. Refer to **PROFILING.md** for profiling usage and output details
8. Refer to **EXPERT_GENERATE.md** when running `makora expert-generate`
9. Refer to **DOCUMENT_SEARCH.md** when running `makora document-search`

## Reference Files

- **FORMATTING.md**: Required file formats for problem and solution files
- **EVALUATION.md**: Command usage and CLI examples
- **PROFILING.md**: How to profile kernels for performance bottlenecks
- **EXPERT_GENERATE.md**: Command usage for `makora expert-generate`
- **DOCUMENT_SEARCH.md**: Command usage for `makora document-search`
- **GPUS.md**: Available GPU devices
- **hardware/NVIDIA.md**: Device-selection guidance and valid device names
- **languages/TRITON.md**: Required Triton solution file structure
- **languages/CUDA.md**: Required CUDA solution file structure
