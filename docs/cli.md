# CLI Reference

SILO comes with a suite of commands to manage your skills.

## `silo init`
Scaffold a new skill directory.

**Usage:**
```bash
silo init <namespace>
```

## `silo install`
Install a local skill folder to the SILO hub.

**Usage:**
```bash
silo install <path_to_skill_folder>
```

## `silo remove`
Uninstall a skill and securely wipe its secrets from the Keychain.

**Usage:**
```bash
silo remove <namespace>
```

## `silo ps`
List all currently installed skills in your hub.

**Usage:**
```bash
silo ps
```

## `silo run`
Execute a specific tool within a skill.

**Usage:**
```bash
silo run <namespace> <tool_name> [args...]
```

## `silo inspect`
Display the instructions and available tools for a specific skill.

**Usage:**
```bash
silo inspect <namespace>
```

## `silo mcp run`
Launch the MCP (Model Context Protocol) router to connect your skills to AI Desktop Agents (like Claude Desktop).

**Usage:**
```bash
silo mcp run
```

## `silo prune`
Remove all installed skills from the hub.

**Usage:**
```bash
silo prune
```
