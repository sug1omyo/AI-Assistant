---
name: chat-ui-sync
description: "Keep the chat UI synchronized with backend routes, tool selectors, mode selectors, and response rendering for the core chatbot. Use when: adding or changing a UI control that calls a backend route, modifying a tool or mode selector, changing a route that the frontend depends on, debugging broken rendering or missing UI state, reviewing whether a functional change needs a UI update, or checking that the frontend and backend agree on payload field names."
---

# Chat UI Sync

## When to use this skill

- Adding, renaming, or removing a UI control that calls a backend route.
- Changing a tool button or mode/model selector in the frontend.
- Modifying a backend route's URL, method, or payload field that the frontend consumes.
- Debugging broken response rendering, missing loading states, or dead buttons.
- Reviewing whether a "backend-only" change requires a matching frontend update.
- Adding a new tool to the tools menu dropdown.
- Changing SSE event data that the message renderer consumes.

## Do not use for

- Pure CSS/visual changes that touch no JS logic and no backend routes.
- Image pipeline or ComfyUI UI (those services have separate frontends).
- FastAPI path changes (parallel implementation — sync separately if needed).

---

## UI-to-route tracing workflow

**Every functional UI change MUST follow this sequence:**

```
1. IDENTIFY the UI control being changed        (HTML element + ID/class)
2. TRACE the JS handler                          (which module, which function)
3. TRACE the backend route                       (URL, method, payload fields)
4. CHECK payload field agreement                  (frontend key names ↔ backend data.get() keys)
5. CHECK response field agreement                 (backend return keys ↔ frontend callback keys)
6. IMPLEMENT change in both layers               (or confirm only one layer needs editing)
7. VERIFY with UI sync checklist                  (Section 11 below)
```

**Rule — mention both files:** When describing a functional change, always name the frontend file(s) AND the backend file(s) involved. A change to `main.js` that affects `tools` payload must acknowledge `stream.py` reads `data.get('tools', [])`.

**Rule — no visual-only edits for functional tasks:** If the user asks to "fix the search button" or "add a new tool," do not make CSS-only changes. Trace the full path: HTML element → JS event → backend route → response rendering.

---

## Architecture overview

The chat UI is a three-layer system:

```
┌─────────────────────────────────────────────────────────┐
│  UI Layer (HTML + CSS)                                  │
│  templates/index.html — controls, inputs, layout        │
│  static/css/app.css   — styling                         │
├─────────────────────────────────────────────────────────┤
│  Handler Layer (JavaScript modules)                     │
│  main.js           — orchestration, event bindings      │
│  api-service.js    — fetch + SSE communication          │
│  chat-manager.js   — localStorage persistence           │
│  message-renderer.js — markdown → DOM rendering         │
│  ui-utils.js       — theme, sidebar, accessibility      │
│  image-gen-v2.js   — image gen modal                    │
│  video-gen.js      — video gen modal                    │
│  memory-manager.js — memory CRUD                        │
│  mcp.js            — MCP sidebar                        │
├─────────────────────────────────────────────────────────┤
│  Backend Layer (Flask routes)                           │
│  routes/stream.py  — POST /chat/stream (SSE)           │
│  routes/main.py    — /, /chat, /clear, /history         │
│  routes/image_gen.py — /api/image-gen/*                 │
│  routes/memory.py  — /api/memory/*                      │
│  routes/conversations.py — /conversations/*             │
│  routes/mcp.py     — /api/mcp/*                         │
│  routes/models.py  — model catalog                      │
│  routes/auth.py    — /api/auth/*                        │
└─────────────────────────────────────────────────────────┘
```

**Data flow:**
```
User action → event listener (main.js) → API call (api-service.js) → Flask route
    ← SSE events / JSON response ← callbacks ← message-renderer.js ← DOM update
```

---

## Safe-touch and avoid zones

### Safe to edit (with tracing)

| Layer | Files | Notes |
|-------|-------|-------|
| Template | `services/chatbot/templates/index.html` | All UI controls, inline tool-binding scripts |
| JS modules | `services/chatbot/static/js/main.js` | Orchestration, `sendMessage()`, event setup |
| JS modules | `services/chatbot/static/js/modules/api-service.js` | Payload assembly, SSE parsing |
| JS modules | `services/chatbot/static/js/modules/chat-manager.js` | localStorage persistence |
| JS modules | `services/chatbot/static/js/modules/message-renderer.js` | Response rendering |
| JS modules | `services/chatbot/static/js/modules/ui-utils.js` | Theme, sidebar state |
| JS modules | `services/chatbot/static/js/modules/image-gen-v2.js` | Image gen modal |
| JS modules | `services/chatbot/static/js/modules/video-gen.js` | Video gen modal |
| JS modules | `services/chatbot/static/js/modules/memory-manager.js` | Memory UI |
| JS modules | `services/chatbot/static/js/mcp.js` | MCP sidebar |
| CSS | `services/chatbot/static/css/app.css` | Styling only |
| Routes | `services/chatbot/routes/*.py` | All chatbot routes |
| Core | `services/chatbot/core/stream_contract.py` | SSE complete event builder |

### Avoid zones

| Zone | Why |
|------|-----|
| `ComfyUI/`, `image_pipeline/` | Separate UI stack |
| `services/stable-diffusion/`, `services/edit-image/` | Image services |
| `services/chatbot/fastapi_app/` | Parallel implementation — sync separately |
| `templates/admin.html`, `templates/login.html` | Admin/auth UI, not part of chat flow |

---

## UI control → backend route map

### Primary chat flow

| UI Control | Element ID | JS Module | Backend Route | Payload Field(s) |
|------------|-----------|-----------|---------------|-------------------|
| Send button | `#sendBtn` | `main.js` → `sendMessage()` | `POST /chat/stream` | Full payload (see Section 5) |
| Message input | `#messageInput` | `main.js` (Enter key) | `POST /chat/stream` | `message` |
| Stop button | `#stopGenerationBtn` | `main.js` → `AbortController.abort()` | — (client-side cancel) | — |
| Clear chat | `#clearBtn` | `main.js` | — (localStorage only) | — |
| New chat | `#newChatBtn` | `chat-manager.js` | — (localStorage only) | — |

### Model and mode selectors

| UI Control | Element ID | Storage | Backend Field |
|------------|-----------|---------|---------------|
| Model selector | `#modelDropdown` items `[data-model]` | `#modelSelect` hidden select + `#modelSelectorLabel` | `model` |
| Thinking mode | `#thinkingModeDropdown` items `[data-mode]` | `#thinkingModeValue` hidden input | `thinking_mode` |
| Context | `#contextSelect` (hidden) | Always `"casual"` | `context` |

### Tool buttons

| UI Button ID | Frontend Tool Name | Backend `tools[]` Value | Backend Handler Location |
|--------------|-------------------|------------------------|--------------------------|
| `#imageGenToolBtn` | `image-generation` | Routed client-side to image-gen-v2 | `main.js` L584 (client-side routing) |
| `#img2imgToolBtn` | `img2img` | Routed client-side to img2img flow | `main.js` L875 |
| `#googleSearchBtn` | `google-search` | `google-search` | `stream.py` L111 |
| `#deepResearchToolBtn` | `deep-research` | `deep-research` | `stream.py` L111 (triggers web search + multi-thinking) |
| `#githubBtn` | `github` | `github` | `stream.py` (via tools dispatch) |
| `#saucenaoBtn` | `saucenao` | `saucenao` | `stream.py` L347 |
| `#googleLensBtn` | `serpapi-reverse-image` | `serpapi-reverse-image` | `stream.py` L369 |
| `#serpapiBingBtn` | `serpapi-bing` | `serpapi-bing` | `stream.py` L387 |
| `#serpapiBaiduBtn` | `serpapi-baidu` | `serpapi-baidu` | `stream.py` L402 |
| `#serpapiImagesBtn` | `serpapi-images` | `serpapi-images` | `stream.py` L417 |

**Tool binding source:** `index.html` inline script, `setupToolItemClicks()` function (~L1858). The `toolBindings` array maps button IDs → tool string names.

**Tool state:** `activeTools` Set in `index.html` inline script, exposed globally via `window.getActiveTools()`. `main.js` reads: `window.getActiveTools ? window.getActiveTools() : Array.from(this.activeTools)`.

### Feature-specific routes

| Feature | JS Module | Backend Route | Method |
|---------|-----------|---------------|--------|
| Image gen | `image-gen-v2.js` | `/api/image-gen/generate` | POST |
| Image meta | `main.js` | `/api/image-gen/meta/<id>` | GET |
| Image save | `main.js` | `/api/image-gen/save/<id>` | POST |
| Image gallery | `main.js` | `/api/storage/images` | GET |
| Video gen | `video-gen.js` | `/api/video/generate` | POST |
| Memory save | `memory-manager.js` | `/api/memory/save` | POST |
| Memory load | `memory-manager.js` | `/api/memory/load/<id>` | GET |
| Memory list | `memory-manager.js` | `/api/memory/list` | GET |
| Auth check | `index.html` inline | `/api/auth/me` | GET |
| Quota check | `index.html` inline | `/api/auth/quota` | GET |
| Feature flags | `index.html` inline | `/api/features` | GET |
| MCP resources | `mcp.js` | `/api/mcp/resources` | GET |
| MCP invoke | `mcp.js` | `/api/mcp/invoke` | POST |

---

## `/chat/stream` payload contract

This is the critical contract. The frontend assembles the body in `api-service.js` L112–125, the backend reads it in `stream.py` L247–265.

### Frontend → Backend field mapping

| Frontend key (`api-service.js`) | Backend key (`stream.py`) | Type | Default |
|--------------------------------|---------------------------|------|---------|
| `message` | `message` | str | `""` |
| `model` | `model` | str | `"grok"` |
| `context` | `context` | str | `"casual"` |
| `deep_thinking` | `deep_thinking` | bool (from string) | `false` |
| `thinking_mode` | `thinking_mode` | str | `"auto"` (backend) / `"instant"` (frontend) |
| `history` | `history` | array | `[]` |
| `memory_ids` | `memory_ids` | array | `[]` |
| `mcp_selected_files` | `mcp_selected_files` | array | `[]` |
| `language` | `language` | str | `"vi"` |
| `custom_prompt` | `custom_prompt` | str | `""` |
| `tools` | `tools` | array of strings | `[]` |
| `images` | `images` | array of base64 data URLs | `[]` |

**Known quirk — `thinking_mode` default mismatch:** Frontend defaults to `"instant"`, backend defaults to `"auto"`. Both resolve to `deep_thinking = false`, so behavior matches. Do not "fix" this by changing either default without testing both paths.

---

## SSE event → frontend callback map

| SSE Event | Frontend Callback | Renderer Method | Key Data Fields |
|-----------|-------------------|-----------------|-----------------|
| `metadata` | (informational, not dispatched to named callback) | — | `model`, `context`, `thinking_mode`, `web_search` |
| `thinking_start` | `callbacks.onThinkingStart(data)` | `createThinkingSection()` | `category`, `timestamp`, `[mode]`, `[label]` |
| `thinking` | `callbacks.onThinking(data)` | `addThinkingStep()` | `step`, `step_index`, `is_reasoning_chunk`, `[trajectory_id]` |
| `thinking_end` | `callbacks.onThinkingEnd(data)` | `endThinkingBlock()` | `summary`, `steps`, `duration_ms`, `[rounds]` |
| `chunk` | `callbacks.onChunk(data)` | `appendChunk()` | `content`, `chunk_index` |
| `complete` | `callbacks.onComplete(data)` | `finalizeMessage()` | 15 fields from `build_complete_event_payload()` |
| `error` | `callbacks.onError(data)` | Error display | `error`, `[request_id]` |
| `suggestions` | `callbacks.onSuggestions(data)` | Suggestion chips | (not yet implemented) |

---

## Model selector binding details

**HTML:** `index.html` L523–630. Items are `div.model-dropdown__item[data-model]` inside `#modelDropdown`.

**Current models in HTML:**

| `data-model` | Display Label |
|--------------|--------------|
| `grok` | Grok-3 |
| `deepseek-reasoner` | DeepSeek R1 |
| `openai` | GPT-4o-mini |
| `deepseek` | DeepSeek V3 |
| `gemini` | Gemini 2.5 Flash |
| `step-flash` | Step-2 Flash |
| `bloomvn` | BloomVN |
| `qwen` | Qwen 3 |
| `stepfun` | Step-2-16k |

**JS binding:** `index.html` inline script (~L1715). Click handler reads `data-model`, updates `#modelSelectorLabel` text, sets `#modelSelect` hidden select value, stores `.active` class.

**Backend reads:** `data.get('model', 'grok')` in `stream.py` L248.

**Adding a new model:**
1. Add `<div class="model-dropdown__item" data-model="new-id">` in `index.html` inside `#modelDropdown`.
2. Ensure `core/config.py` has the API key configured for the provider.
3. Ensure `core/chatbot.py` routes `model="new-id"` to the correct provider.
4. Update `routes/models.py` `MODEL_CATALOG` if used.
5. No JS module changes needed — the inline click handler is generic.

---

## Thinking mode selector binding details

**HTML:** `index.html` L640–665. Options are `div.thinking-mode-option[data-mode]` inside `#thinkingModeDropdown`.

**Current modes:**

| `data-mode` | `data-icon` | `data-label` | Backend mapping |
|-------------|-------------|-------------|-----------------|
| `instant` | `zap` | Instant | `deep_thinking = false` |
| `multi-thinking` | `layers` | 4-Agents | `deep_thinking = true` |

**JS binding:** `index.html` inline script (~L1762). `selectThinkingMode(mode, icon, label)` updates `#thinkingModeValue`, `#thinkingModeLabel`, `#thinkingModeIcon`, saves to `localStorage.thinkingMode`.

**Backend reads:** `data.get('thinking_mode', 'auto')` in `stream.py` L260. Maps to `deep_thinking` boolean at L261–265.

**Note:** Only `instant` and `multi-thinking` are exposed in the current UI. Backend also supports `thinking`, `deep`, and `auto` but these have no UI selectors.

---

## Tool activation flow

```
User clicks tool button (e.g., #googleSearchBtn)
  → index.html: setupToolItemClicks() reads toolBindings array
  → toggleToolActive('google-search', buttonElement)
  → activeTools Set: add/remove 'google-search'
  → updateActiveToolsDisplay() → shows badge in #activeToolsDisplay
  → window.getActiveTools() now returns ['google-search']
  
User clicks Send:
  → main.js L580: activeTools = window.getActiveTools()
  → main.js L1123: passed as tools: activeTools to sendStreamMessage()
  → api-service.js L124: body.tools = params.tools
  → POST /chat/stream with body { ..., tools: ['google-search'] }
  → stream.py L321: tools = data.get('tools', [])
  → stream.py L111: if "google-search" in tools → runs web search
```

**Deep Research special case:** When `deep-research` is activated, the inline handler also: (1) auto-enables `google-search`, (2) switches thinking mode to `multi-thinking`.

**Image generation routing:** `image-generation` and `img2img` tools are intercepted client-side in `main.js` before reaching `/chat/stream`. They route to dedicated image/video gen flows.

---

## Loading, disabled, and error states

### During streaming

| Element | State Change | Reverted On |
|---------|-------------|-------------|
| `#sendBtn` | `.disabled = true` | `complete` or `error` event |
| `#messageInput` | `.disabled = true` | `complete` or `error` event |
| Loading indicator | Shown (typing dots animation) | `complete` or `error` event |
| `#stopGenerationBtn` | Visible | `complete` or `error` event |
| Stream message div | Created, hidden until first `chunk` | First `chunk` shows it |

### Error states

| Error Source | UI Behavior |
|-------------|-------------|
| SSE `error` event | Error message rendered in chat, send re-enabled |
| Fetch failure (network) | Exception caught, error displayed, send re-enabled |
| Abort (user stop) | Stream cancelled, partial response preserved |

### Stale state risk

If a stream completes but the `complete` callback fails to fire (e.g., malformed JSON), the UI may remain in loading state with send button disabled. The `finally` block in `sendMessage()` handles re-enabling, but verify this path when changing response shapes.

---

## Element IDs that JS depends on

These IDs are read or written at runtime. Renaming them breaks functionality.

**Critical (send flow):**
- `#messageInput` — value read, disabled toggled
- `#sendBtn` — disabled toggled
- `#chatContainer` — messages appended
- `#thinkingModeValue` — value read for payload
- `#modelSelect` — value read for payload (hidden select)

**Selectors:**
- `#modelSelectorBtn`, `#modelDropdown`, `#modelSelectorLabel` — model picker
- `#thinkingModeBtn`, `#thinkingModeDropdown`, `#thinkingModeLabel`, `#thinkingModeIcon` — mode picker
- `#toolsMenuBtn`, `#toolsMenuDropdown` — tools grid
- `#activeToolsDisplay` — active tool badges

**Tool buttons (from `toolBindings` array):**
- `#imageGenToolBtn`, `#img2imgToolBtn`, `#googleSearchBtn`, `#deepResearchToolBtn`, `#githubBtn`, `#saucenaoBtn`, `#googleLensBtn`, `#serpapiBingBtn`, `#serpapiBaiduBtn`, `#serpapiImagesBtn`

**State:**
- `#stopGenerationBtn` — stop streaming
- `#darkModeBtn`, `#eyeCareBtn` — theme
- `#sidebarToggleBtn` — sidebar
- `#newChatBtn` — new conversation
- `#fileInput` — file upload

---

## CSS classes that JS depends on for logic

| Class | Used For (logic, not styling) | Module |
|-------|------------------------------|--------|
| `.active` | Mark selected model/mode/tool | `index.html` inline |
| `.hidden` | Show/hide dropdowns & modals | Multiple |
| `.open` | Toggle tools dropdown visibility | `index.html` inline |
| `.collapsed` | Sidebar state | `ui-utils.js` |
| `.light-mode` | Theme detection | `ui-utils.js` |
| `.eye-care-mode` | Theme detection | `ui-utils.js` |
| `.streaming-cursor` | Active streaming indicator | `main.js` |

---

## Global window variables the UI relies on

| Variable | Set By | Read By | Purpose |
|----------|--------|---------|---------|
| `window.chatApp` | `main.js` init | Multiple modules | Main app instance |
| `window.chatManager` | `main.js` init | `chat-manager.js` consumers | Chat session manager |
| `window.__CHAT_FEATURES` | `index.html` inline | `message-renderer.js` | Feature flags |
| `window.mcpController` | `mcp.js` | `api-service.js` | MCP selected files |
| `window.getThinkingMode` | `index.html` inline | `api-service.js` | Current thinking mode getter |
| `window.getActiveTools` | `index.html` inline | `main.js` | Active tools getter |
| `window.customPromptEnabled` | `index.html` inline | `main.js` | Custom prompt toggle |
| `window.removeTool` | `index.html` inline | `index.html` onclick | Remove tool badge |

---

## localStorage keys the UI depends on

| Key | Type | Purpose |
|-----|------|---------|
| `chatSessions` | JSON string | All conversations + messages |
| `chatbot_language` | `"vi"` / `"en"` | Language sent in payload |
| `theme` | string | Dark/light/eye-care |
| `sidebarCollapsed` | `"1"` / `"0"` | Sidebar open/closed |
| `thinkingMode` | string | Persisted thinking mode selection |
| `thinkingStateByRequest` | JSON string | Collapse state for thinking blocks |
| `chatFeatureFlags` | JSON string | `__CHAT_FEATURES` overrides |

---

## Common pitfalls

### Pitfall 1: Adding a tool button without a backend handler

❌ Add `<button id="newToolBtn">` + entry in `toolBindings` → tool name gets sent in `tools[]` → backend ignores it silently.

✅ Also add handler in `stream.py` like the existing `if 'tool-name' in tools:` blocks.

### Pitfall 2: Renaming a route URL only in backend

❌ Change `/api/memory/save` to `/api/memories` in `memory.py` → `memory-manager.js` still fetches old URL → 404.

✅ Update both the route in `memory.py` AND the fetch URL in `memory-manager.js`.

### Pitfall 3: Adding a payload field only in frontend

❌ Add `body.newField = value` in `api-service.js` but never read `data.get('newField')` in `stream.py` → field is silently dropped.

✅ Add reading logic in the backend route handler.

### Pitfall 4: Changing an element ID without updating `toolBindings`

❌ Rename `#googleSearchBtn` to `#webSearchBtn` in HTML → `setupToolItemClicks()` looks for `#googleSearchBtn` → `document.getElementById` returns null → no event listener → button is dead.

✅ Update both the HTML ID and the `toolBindings` array entry.

### Pitfall 5: CSS-only edit that accidentally breaks logic

❌ Remove `.active` class styling → class is still toggled by JS → visually no highlight but logically the tool IS selected → user confusion.

✅ Keep the class; only change its visual styles.

### Pitfall 6: Changing thinking mode options without backend mapping

❌ Add `data-mode="deep-think"` in HTML → `selectThinkingMode('deep-think', ...)` stores the value → backend reads `thinking_mode = 'deep-think'` → falls through to default, unexpected behavior.

✅ Check `stream.py` L261–265 to ensure the backend maps the new mode value correctly.

---

## Compatibility note for existing controls

The existing UI controls are functional and battle-tested. When modifying them:

1. **Model selector options are hardcoded in HTML.** Adding/removing a model requires editing `index.html`. The JS handler is generic — it reads `data-model` from any child of `#modelDropdown`.

2. **Thinking mode options are hardcoded in HTML.** Only `instant` and `multi-thinking` are exposed. Backend supports more modes but they are intentionally hidden from the UI.

3. **Tool button bindings are in an inline script.** The `toolBindings` array in `index.html` (~L1858) is the single source of truth for button ID → tool name mapping. Do not add tool click handlers in `main.js` that duplicate this.

4. **`activeTools` Set lives only in the inline script scope.** It is exposed globally via `window.getActiveTools()`. `main.js` has its own `this.activeTools` Set that is used as a fallback if `window.getActiveTools` is undefined. Do not assume one is always authoritative — check both.

5. **`deep_thinking` boolean is legacy but still sent.** Frontend computes it from `thinkingMode`, backend also derives it from `thinking_mode`. Do not remove `deep_thinking` from the payload — older code paths may still reference it.

6. **Image generation tools bypass `/chat/stream`.** `image-generation` and `img2img` in the `tools[]` array are intercepted client-side in `main.js` and routed to dedicated gen flows. They never reach `stream.py`.

---

## UI sync checklist

Before merging any change that touches both frontend and backend:

- [ ] **Route URL matches between JS and Python** — hardcoded URLs in JS modules match route decorators in `routes/*.py`
- [ ] **Payload field names agree** — `api-service.js` body keys match `stream.py` `data.get()` keys exactly (snake_case)
- [ ] **SSE event type names match** — `stream.py` `_emit('event_name', ...)` matches `api-service.js` `switch(currentEvent)` cases
- [ ] **SSE payload keys match callback expectations** — every key the frontend reads from event data is emitted by the backend
- [ ] **Element IDs unchanged or updated in all references** — HTML ID, JS `getElementById`, `toolBindings` array all agree
- [ ] **Tool name in `toolBindings` matches backend `if 'name' in tools`** — frontend tool string == backend tool string
- [ ] **Model `data-model` values match backend routing** — `chatbot.py` and `config.py` recognize all model IDs in the HTML
- [ ] **Thinking mode `data-mode` values have backend mapping** — `stream.py` L261–265 handles all mode values in the HTML
- [ ] **Loading/disabled states restored on all exit paths** — `complete`, `error`, `abort`, and exception paths all re-enable send
- [ ] **No new hardcoded URLs added** — if adding a new API call, verify the URL exists as a registered route
- [ ] **`window.getActiveTools()` and `this.activeTools` stay in sync** — if modifying tool state, check both inline script and `main.js`
- [ ] **localStorage keys not renamed without migration** — renaming breaks returning users' saved state

---

## File reference

| File | Purpose | Key Locations |
|------|---------|---------------|
| `services/chatbot/templates/index.html` | All HTML controls, inline tool/model/mode binding scripts | L523 (model), L640 (mode), L765 (tools), L1715+ (JS bindings) |
| `services/chatbot/static/js/main.js` | App orchestration, `sendMessage()`, event listeners | L38 (`activeTools`), L580 (tool read), L1112 (`sendStreamMessage` call) |
| `services/chatbot/static/js/modules/api-service.js` | Payload assembly, SSE parsing, fetch calls | L102 (`sendStreamMessage`), L112 (body), L129 (fetch URL) |
| `services/chatbot/static/js/modules/chat-manager.js` | localStorage persistence, session management | `saveSessions()`, `loadSessions()`, `switchChat()` |
| `services/chatbot/static/js/modules/message-renderer.js` | Markdown → DOM, thinking blocks, code highlighting | `addMessage()`, `appendChunk()`, `createThinkingSection()` |
| `services/chatbot/static/js/modules/ui-utils.js` | Theme toggle, sidebar, element caching | `toggleDarkMode()`, `toggleSidebar()`, `initElements()` |
| `services/chatbot/static/js/modules/image-gen-v2.js` | Image gen modal UI | Calls `/api/image-gen/generate` |
| `services/chatbot/static/js/modules/video-gen.js` | Video gen modal UI | Calls `/api/video/generate` |
| `services/chatbot/static/js/modules/memory-manager.js` | Memory save/load/list UI | Calls `/api/memory/*` |
| `services/chatbot/static/js/mcp.js` | MCP sidebar, resource/tool listing | Calls `/api/mcp/*` |
| `services/chatbot/static/css/app.css` | All chat styling | `.active`, `.hidden`, `.open` classes |
| `services/chatbot/routes/stream.py` | SSE streaming, tool dispatch, payload parsing | L247 (payload read), L321 (tools), L111 (search dispatch) |
| `services/chatbot/routes/main.py` | Legacy routes, health check | `/`, `/chat`, `/api/health/databases` |
| `services/chatbot/routes/image_gen.py` | Image generation API | `/api/image-gen/generate` |
| `services/chatbot/routes/memory.py` | Memory CRUD API | `/api/memory/save`, `/list`, `/load/<id>` |
| `services/chatbot/routes/conversations.py` | Conversation CRUD API | `/conversations`, `/conversations/<id>` |
| `services/chatbot/routes/mcp.py` | MCP proxy API | `/api/mcp/resources`, `/invoke` |
| `services/chatbot/core/stream_contract.py` | `build_complete_event_payload()` | L23 |

---

## Related skills

- **tool-response-contract** — exact response shapes for every route, SSE event, and tool function
- **core-chatbot-routing-audit** — Flask blueprint registration and request path tracing
- **search-tool-cascade** — tool fallback order and auto-trigger logic
- **thinking-mode-routing** — thinking mode lifecycle (UI selector → backend → SSE events)
- **provider-env-matrix** — model IDs, API keys, and provider routing
