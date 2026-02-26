# Makora CLI

The Makora CLI is a command-line interface (CLI) for interacting with Makora Generate.

Use it as a standalone tool or with your favourite coding agent!

## Installation and Setup

### Prerequisites
- Python 3.10+
- `pip`

### Install 
```bash
pip install makora
```

or for editable mode (development), after cloning this repo:

```bash
pip install -e .
```

### Verify install
```bash
makora --help
```

## Login Before Using Protected Commands
Most commands require authentication first.

1. Create/copy an API token from:
   `https://generate.makora.com/tokens`

2. Login interactively:
   ```bash
   makora login
   ```
   or non-interactively:
   ```bash
   makora login --token <token_value_or_file_containing_it>
   ```

3. Confirm login state:
   ```bash
   makora info
   ```

To clear credentials:
```bash
makora logout
```

## Subcommands

Below is the summary of available subcommands provided by the package.
For a more comprehensive introduction and overview, please see: https://docs.makora.com.

> **Note:** also try consulting each subcommands `--help`!

| Subcommand | Login required | Purpose |
|---|---|---|
| `login` | No | Save API credentials for CLI use. |
| `logout` | No | Remove saved credentials. |
| `info` | No | Show version, env vars, and current login status. |
| `generate` | Yes | Validate code and create a new optimization session. |
| `jobs` | Yes | List your sessions/jobs. |
| `stop` | Yes | Stop a running job/session. |
| `kernels` | Yes | List kernels for a session or show kernel code. |
| `check` | Yes | Validate a kernel/problem file without creating a full run. |
| `refcode` | Yes | Show the original reference code for a session. |
| `profile` | Yes | Profile optimized vs reference code on remote hardware. |
| `evaluate` | Yes | Benchmark optimized vs reference code on remote hardware. |
| `expert-generate` | Yes | Generate improved kernel code with additional tools. |
| `document-search` | Yes | Search documents via the additional-tools document search API. |
| `install` | Yes | Install the Makora plugin (currently `claude`). |
