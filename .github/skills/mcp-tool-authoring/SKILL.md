---
name: mcp-tool-authoring
description: "Guide changes to the MCP server: adding or modifying tools, resources, and prompts. Use when: adding a new MCP tool, resource, or prompt; changing an existing tool's input/output contract; debugging tool registration or response shape; reviewing MCP server code; checking chatbot-side MCP route compatibility; or updating MCP documentation."
---

# MCP Tool Authoring

## When to use this skill

- Adding a new tool, resource, or prompt to the MCP server.
- Changing an existing tool's parameters, return shape, or error handling.
- Debugging why a tool is not discovered or returns unexpected data.
- Reviewing whether a chatbot-side MCP route needs updating after a server change.
- Updating `services/mcp-server/README.md` after any tool/resource/prompt change.

## Architecture snapshot

| Fact | Value |
|---|---|
| Active server | `services/mcp-server/server.py` |
| FastMCP instance | `mcp = FastMCP("AI-Assistant")` |
| Transport | **stdio only** — never add HTTP listeners |
| SDK import | `from mcp.server.fastmcp import FastMCP` |
| Install | `pip install "mcp[cli]"` (venv-core) |
| Base dir | `BASE_DIR = Path(__file__).parent.parent.parent` (project root) |
| Enhanced variant | `server_enhanced.py` (caching, rate limiting, logging) |
| Advanced utilities | `tools/advanced_tools.py` (plain functions, **not** auto-registered) |
| Chatbot MCP routes | `services/chatbot/routes/mcp.py` → `mcp_bp` blueprint |
| Chatbot MCP client | `services/chatbot/src/utils/mcp_integration.py` |
| Inspector | `npx @modelcontextprotocol/inspector python server.py` |
| CLI test | `python -m mcp.cli server.py` |

## Current registry

### Tools (in `server.py`)

| Tool | Parameters | Return |
|---|---|---|
| `search_files` | `query: str, file_type: str = "all", max_results: int = 10` | `Dict[str, Any]` — `{query, file_type, total_found, results: [...]}` |
| `read_file_content` | `file_path: str, max_lines: int = 100` | `Dict[str, Any]` — `{file_path, total_lines, lines_read, truncated, content}` or `{error}` |
| `list_directory` | `dir_path: str = ".", include_hidden: bool = False` | `Dict[str, Any]` — `{directory, total_items, folders, files}` or `{error}` |
| `get_project_info` | *(none)* | `Dict[str, Any]` — `{project_name, base_directory, services, structure, description}` |
| `search_logs` | `service: str = "all", level: str = "all", last_n_lines: int = 50` | `Dict[str, Any]` — `{service_filter, level_filter, logs_found, data}` or `{error}` |
| `calculate` | `expression: str` | `Dict[str, Any]` — `{expression, result, type}` or `{expression, error}` |

### Resources (in `server.py`)

| URI | Function | Returns |
|---|---|---|
| `config://model` | `get_model_config()` | `str` — file content or error message |
| `config://logging` | `get_logging_config()` | `str` — file content or error message |
| `docs://readme` | `get_readme()` | `str` — file content or error message |
| `docs://structure` | `get_structure_doc()` | `str` — file content or error message |

### Prompts (in `server.py`)

| Prompt | Parameters | Returns |
|---|---|---|
| `code_review_prompt` | `file_path: str` | `str` — review template |
| `debug_prompt` | `error_message: str, context: str = ""` | `str` — debug template |
| `explain_code_prompt` | `code_snippet: str` | `str` — explanation template |

### Unregistered utilities (`tools/advanced_tools.py`)

These are plain functions **not** decorated with `@mcp.tool()` and **not** imported into `server.py`. They exist as available building blocks but do not appear in the MCP tool list:

- `git_status()`, `git_log()`, `git_branch_info()`
- `query_sqlite_database()`, `list_database_tables()`
- `analyze_python_file()`, `find_todos_in_code()`
- `fetch_github_repo_info()`

To expose one: import it in `server.py` and wrap it with `@mcp.tool()`, or add the decorator directly in `advanced_tools.py` and import the `mcp` instance.

## Templates

### New tool template

Add to `server.py` inside the `# ==================== TOOLS ====================` section:

```python
@mcp.tool()
def my_tool_name(required_param: str, optional_param: int = 10) -> Dict[str, Any]:
    """
    One-line description of what this tool does.

    Args:
        required_param: What this parameter means
        optional_param: What this parameter means (default: 10)

    Returns:
        Dict containing the result or an error key
    """
    try:
        # --- implementation ---
        return {
            "required_param": required_param,
            "result": "your data here"
        }
    except Exception as e:
        return {"error": f"Tool failed: {str(e)}"}
```

### New resource template

Add to `server.py` inside the `# ==================== RESOURCES ====================` section:

```python
@mcp.resource("scheme://identifier")
def get_my_resource() -> str:
    """One-line description of the resource."""
    try:
        target = BASE_DIR / "path" / "to" / "file"
        if target.exists():
            with open(target, "r", encoding="utf-8") as f:
                return f.read()
        return "Resource not found"
    except Exception as e:
        return f"Error reading resource: {str(e)}"
```

URI scheme conventions in this repo:
- `config://` — configuration files
- `docs://` — documentation files
- Use a new scheme only if neither fits.

### New prompt template

Add to `server.py` inside the `# ==================== PROMPTS ====================` section:

```python
@mcp.prompt()
def my_prompt_name(context_param: str, optional_param: str = "") -> str:
    """
    One-line description of the prompt.

    Args:
        context_param: What this parameter injects
        optional_param: Optional extra context
    """
    return f"""Your prompt template here.

Context: {context_param}
{f'Extra: {optional_param}' if optional_param else ''}

Instructions:
1. Step one
2. Step two"""
```

## Contracts to enforce

### Input contract
- Use Python type hints on every parameter.
- Provide sensible defaults for optional parameters.
- Validate inputs early; return `{"error": "..."}` for bad inputs, do not raise.
- Never accept raw file system paths without resolving through `BASE_DIR`.

### Output contract — tools
- Always return `Dict[str, Any]`.
- Success shape: include the input echo plus result data.
- Error shape: `{"error": "Human-readable message"}` — never expose stack traces.
- Never return `None` or raise unhandled exceptions.

### Output contract — resources
- Always return `str`.
- On failure, return an error string (not an exception).

### Output contract — prompts
- Always return `str`.
- Include parameter-injected content clearly.
- Keep the template self-contained; the caller doesn't have access to server internals.

### Security rules
- Resolve all paths through `BASE_DIR`. Do not allow path traversal.
- Do not execute arbitrary shell commands from tool inputs.
- Do not expose API keys, secrets, or `.env` contents through resources.
- Skip `venv*`, `__pycache__`, `.git`, `node_modules` when traversing directories.

## Scope assessment — MCP-only or cross-cutting?

Before implementing, determine if the change stays within the MCP server or also affects the chatbot side.

| Scope | What to update |
|---|---|
| **MCP-only** (new tool used only through MCP clients like Claude Desktop / Inspector) | `server.py`, `services/mcp-server/README.md` |
| **MCP + chatbot proxy** (chatbot UI needs access to the new tool) | All MCP-only files + `routes/mcp.py` (add a Flask route) + `src/utils/mcp_integration.py` (add client method) + possibly `templates/index.html` (add UI trigger) |
| **Promoting an advanced_tools utility** | `server.py` (import + decorator or wrapper) + `services/mcp-server/README.md` |

## Implementation checklist

- [ ] **1. Identify scope**: MCP-only, MCP + chatbot, or promoting an existing utility.
- [ ] **2. Choose the right file**: `server.py` for direct tools/resources/prompts. If the function is large and reusable, put the logic in `tools/advanced_tools.py` and import + decorate in `server.py`.
- [ ] **3. Add the function** using the template above. Place it in the correct section (`TOOLS`, `RESOURCES`, or `PROMPTS`).
- [ ] **4. Follow naming**: `snake_case` for tool/prompt function names. `scheme://identifier` for resource URIs.
- [ ] **5. Type all parameters** with Python type hints. Provide defaults for optional params.
- [ ] **6. Return the correct shape**: `Dict[str, Any]` for tools, `str` for resources and prompts.
- [ ] **7. Handle errors**: wrap body in try/except, return `{"error": "..."}` for tools or an error string for resources. Never raise.
- [ ] **8. Validate paths**: resolve through `BASE_DIR`, check existence before reading, skip excluded dirs.
- [ ] **9. If MCP + chatbot**: add a route in `routes/mcp.py`, add a client method in `src/utils/mcp_integration.py`.
- [ ] **10. Update README**: add the tool/resource/prompt to the feature list in `services/mcp-server/README.md`.
- [ ] **11. Update main README** (if the tool is user-facing or changes the service map).

## Verification checklist

- [ ] **Inspector test**: run `npx @modelcontextprotocol/inspector python server.py` and confirm the new tool/resource/prompt appears in the discovery list.
- [ ] **Call test**: invoke the tool/resource/prompt through the inspector and verify the response shape matches the documented contract.
- [ ] **Error path**: invoke with invalid inputs (missing required param, bad path, out-of-range value) and verify the error shape is `{"error": "..."}`.
- [ ] **Path traversal**: if the tool reads files, test with `../../etc/passwd` or similar and confirm it is rejected or resolves safely within `BASE_DIR`.
- [ ] **Existing tools unbroken**: confirm all 6 existing tools still appear and respond correctly after the change.
- [ ] **Chatbot-side** (if cross-cutting): start the chatbot, call the proxy route, and confirm the response arrives correctly.
- [ ] **README accuracy**: tool name, parameters, and return shape in `services/mcp-server/README.md` match the implementation.
- [ ] **Transport**: confirm no HTTP listener was added — the server runs on stdio only.
- [ ] **No env leak**: confirm no tool or resource exposes `.env` file contents or API key values.

## Common mistakes

| Mistake | Why it's wrong | Fix |
|---|---|---|
| Forgetting `-> Dict[str, Any]` return type | Breaks type consistency; callers expect dict | Add return annotation |
| Returning `None` on error | MCP client receives null instead of an explanation | Return `{"error": "msg"}` |
| Using `os.path.join(user_input)` without validation | Path traversal vulnerability | Resolve through `BASE_DIR`, check `is_relative_to` |
| Adding `@mcp.tool()` in `advanced_tools.py` without importing `mcp` | Decorator references an undefined name | Either import the `mcp` instance from `server.py` (circular risk) or wrap in `server.py` |
| Adding `app.run()` or HTTP listener | Breaks the stdio-only transport contract | Never add HTTP; MCP uses stdio |
| Not updating `README.md` | Tool exists but isn't documented | Always update `services/mcp-server/README.md` |
| Hardcoding absolute paths | Breaks on other machines | Use `BASE_DIR / "relative/path"` |

## Touch map

| Action | Files to touch |
|---|---|
| Add MCP tool | `server.py`, `services/mcp-server/README.md` |
| Add MCP resource | `server.py`, `services/mcp-server/README.md` |
| Add MCP prompt | `server.py`, `services/mcp-server/README.md` |
| Promote utility from `advanced_tools.py` | `server.py` (import + register), `services/mcp-server/README.md` |
| Expose MCP tool to chatbot UI | `server.py`, `routes/mcp.py`, `src/utils/mcp_integration.py`, `templates/index.html`, `services/mcp-server/README.md` |
| Change tool return shape | `server.py`, caller routes in `routes/mcp.py` (if proxied), `services/mcp-server/README.md` |
| Change server startup | `server.py` (`main()`), `start-mcp-server.bat`, `start-mcp-server.sh`, `services/mcp-server/README.md` |

## Required output format

When responding after using this skill, structure the answer as:

- **Scope**: MCP-only / MCP + chatbot / utility promotion
- **What was added or changed**: tool name, resource URI, or prompt name
- **Input contract**: parameters with types and defaults
- **Output contract**: success shape and error shape
- **Files touched**: list with brief reason
- **Verification steps**: commands to run
- **Doc updates needed**: which READMEs were or should be updated
