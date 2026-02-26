# Using Makora Document Search

The `makora document-search` CLI command searches indexed documents via Makora additional tools.

## Command Invocation

```bash
makora document-search <query> [options]
```

## Options

- `query` (required): Search query string (must be non-empty)
- `--max-entries` or `-n`: Maximum number of documents to return (range: `1-49`, default: `5`)

## Output Behavior

- Prints `Searching documents...` while the request is running.
- If matches are found, prints `Found N document(s):` followed by entries.
- Each entry may include:
  - `id` (always expected)
  - `score` (optional)
  - `meta` JSON (optional)
  - `content` (optional)
- If no matches are found, prints `No documents found.`

## Examples

```bash
makora document-search "flash attention"
makora document-search "warp specialization" --max-entries 10
makora document-search "triton shared memory" -n 3
```
