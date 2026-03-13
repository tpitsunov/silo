# SILO Framework

Welcome to the documentation for SILO — the trust layer for modern AI tool execution.

## What is SILO?

SILO is a robust execution engine and package manager for AI Agent tools (skills). Unlike traditional tool frameworks, SILO emphasizes:

- **🔒 Isolation**: Every skill runs in its own `uv` virtual environment.
- **🛡️ Security**: Secrets are encrypted with AES-256-GCM and injected via STDIN.
- **🧩 Dynamic Routing**: Agents search for tools semantically using BM25 and exact matching.
- **✨ Premium DX**: Browser-based approvals and interactive auth flows.

## Getting Started

Install the core framework:

```bash
uv tool install silo-framework
```

Initialize your first skill:

```bash
silo init my-skill
```

## Why SILO?

SILO helps developers bring their ideas to life by conquering the complexity of AI tool development. It provides a trusted starting point for every agent integration, ensuring that tools are discoverable, secure, and reproducible across any environment.
