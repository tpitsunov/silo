# SILO Framework

<p align="center">
  <img src="logo.png" width="200" alt="SILO Logo">
</p>

Welcome to the documentation for **SILO** — the trust layer for modern AI tool execution.

## What is SILO?

SILO (Secure, Isolated, Lightweight, Offloaded) is a robust execution engine and package manager for AI Agent tools (skills). It solves the "last mile" problem of agentic workflows by providing a secure, predictable environment for tools to run.

!!! success "Core Pillars"
    - **🔒 Isolation**: Every skill runs in its own isolated `uv` virtual environment. No more dependency hell.
    - **🛡️ Security**: Secrets are encrypted at rest and injected via STDIN. They never leak to the LLM or logs.
    - **🧩 Discovery**: Agents find tools semantically using BM25. No more hallucinating tool names.
    - **✨ Premium DX**: Built-in browser-based approvals and interactive auth flows.

## Quick Start

Install the core framework using `uv`:

```bash
uv tool install silo-framework
```

Initialize your first skill:

```bash
silo init my-skill
```

## Why SILO?

SILO helps developers bring their ideas to life by conquering the complexity of AI tool development. It provides a trusted starting point for every agent integration, ensuring that tools are discoverable, secure, and reproducible across any environment.

---

[Get Started with the Tutorial →](tutorials/first-skill.md){ .md-button .md-button--primary }
