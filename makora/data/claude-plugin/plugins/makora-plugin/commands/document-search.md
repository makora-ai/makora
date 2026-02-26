---
description: Search indexed documents with makora document-search
argument-hint: <query> [--max-entries count]
allowed-tools: Bash(*), Read(*), Glob(*)
---

# Makora Document Search

Search indexed documents using Makora's document search capability.

Always make sure to activate the installed Makora skill first.

## Task

You will run document search through the Makora skill (`makora-plugin:makora-skill`).

### Arguments

- `$1`: Search query string (required)
- `$2` (optional): `--max-entries <int>` or `-n <int>`

If arguments are not provided, ask the user for:
1. Query string
2. Maximum number of entries to return (default: 5)

## Instructions

- Refer to the Makora skill documentation (specifically **DOCUMENT_SEARCH.md**) for command behavior, option constraints, and output details.

## Example Usage

```bash
/makora-plugin:document-search "flash attention tiling"
/makora-plugin:document-search "warp-level reduction" --max-entries 10
/makora-plugin:document-search "tensor core mma" -n 3
```
