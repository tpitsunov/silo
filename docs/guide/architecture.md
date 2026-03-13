# Architecture Overview

SILO is built as a modular execution layer for AI Agents. It provides a trusted tool ecosystem where the framework manages the lifecycle of tools, ensuring they are secure, isolated, and easy to discover.

## Core Components

### 1. The Hub (Skill Registry)
The Hub is a local database and file storage (located in `~/.silo/`) that tracks all installed skills.
- It stores metadata about tool names, descriptions, and required arguments.
- It maintains the LRU (Least Recently Used) cache for efficient cleanup during pruning.

### 2. The Runner (Execution Engine)
The Runner is responsible for the actual execution of tools.
- **Local Virtual Environments**: Every skill in the hub maintains its own `.venv` directory. This ensures full dependency isolation and allows `uv` to use hard-links to save disk space while providing a portable, project-like environment for each skill.
- **Process Isolation**: It spawns isolated Python processes using the skill's specific interpreter. This bypasses global `uv run` checks on every call, significantly improving execution speed.
- **IPC (Inter-Process Communication)**: It communicates with the child process via pipes, safely injecting secrets and receiving responses.
- **Result Handling**: It parses standardized outputs (`AgentResponse`) and handles errors or approval requests.

### 3. The Search Engine (Discovery)
When an Agent doesn't know which tool to use, the Search Engine provides semantic matching.
- **BM25 Algorithm**: High-performance text ranking based on tool descriptions.
- **Dynamic Routing**: Allows Agents to search for "what" they want to do rather than "how".

### 4. The Interactive Layer (HITL)
A specialized module that handles human-in-the-loop approvals and secret collection.
- **Browser-Based**: Spawns a local HTML interface for a premium user experience.
- **Terminal-Based**: Fallback for SSH and remote environments.

## Flow of Execution

1. **Discovery**: Agent queries `silo_search`.
2. **Selection**: Agent selects a tool based on the returned schema.
3. **Trigger**: Agent calls `silo_execute`.
4. **Validation**: Runner checks for required secrets and user approvals.
5. **Execution**: Sandbox process runs the logic and returns a structured response.
6. **Persistence**: Hub updates usage history.
