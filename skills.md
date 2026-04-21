# skills.md — Local Image Stack Guide for AI-Assistant

Practical operator / developer guide for the **local image generation stack**
in this repository. Intended for future Copilot / Claude sessions so they
can work on the repo without rebuilding the image system from scratch.

The authoritative per-task skill files live under `.github/skills/`. This
document is a higher-level map for the local anime/image pipeline only.

---

## 1. Purpose

The local image stack exists to:

- run **local or hybrid image generation** through the repo's existing
  image orchestration paths,
- support the **anime pipeline** under `image_pipeline/anime_pipeline/`,
- integrate **ComfyUI-based workflows**, structured planning,
  critique / refine loops, and local debugging artifacts,
- preserve backward compatibility with existing chatbot and
  image-generation routes.

This is **not** a greenfield stack. Always audit what already exists in the
current branch before adding or rewriting modules.

---

## 2. Critical-path files

First places to inspect before any change.

### Top-level docs and repo conventions

- `README.md`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/skills/`
- `app/requirements/profile_core_services.txt`
- `app/requirements/profile_image_ai_services.txt`
- `app/requirements/README.md`

### Local image orchestration and entry points

- `services/chatbot/core/image_gen/`
- `services/chatbot/routes/image_gen.py`
- `services/chatbot/routes/anime_pipeline.py` (Flask blueprint)
- `services/chatbot/fastapi_app/routers/anime_pipeline.py` (FastAPI mirror)
- `services/chatbot/core/anime_pipeline_service.py` (service layer)

### Anime / local pipeline core

- `image_pipeline/anime_pipeline/orchestrator.py`
- `image_pipeline/anime_pipeline/schemas.py`
- `image_pipeline/anime_pipeline/config.py`
- `image_pipeline/anime_pipeline/workflow_builder.py`
- `image_pipeline/anime_pipeline/comfy_client.py`
- `image_pipeline/anime_pipeline/vision_service.py`
- `image_pipeline/anime_pipeline/result_store.py`
- `image_pipeline/anime_pipeline/workflow_serializer.py`
- `image_pipeline/anime_pipeline/lora_manager.py`
- `image_pipeline/anime_pipeline/character_references.py`
- `image_pipeline/anime_pipeline/character_research.py`
- `configs/anime_pipeline.yaml`
- `configs/anime_pipeline_example.yaml`
- `configs/lora_registry.yaml`

### Agent / stage files

- `image_pipeline/anime_pipeline/agents/vision_analyst.py`
- `image_pipeline/anime_pipeline/agents/layer_planner.py`
- `image_pipeline/anime_pipeline/agents/composition_pass.py`
- `image_pipeline/anime_pipeline/agents/structure_lock.py`
- `image_pipeline/anime_pipeline/agents/cleanup_pass.py`    *(standalone; not on the live stage sequence — see §6)*
- `image_pipeline/anime_pipeline/agents/beauty_pass.py`
- `image_pipeline/anime_pipeline/agents/critique.py`
- `image_pipeline/anime_pipeline/agents/refine_loop.py`     *(standalone; orchestrator uses its own in-line loop — see §6)*
- `image_pipeline/anime_pipeline/agents/upscale.py`
- `image_pipeline/anime_pipeline/agents/final_ranker.py`
- `image_pipeline/anime_pipeline/agents/output_manifest.py`
- `image_pipeline/anime_pipeline/agents/detection_detail.py`
- `image_pipeline/anime_pipeline/agents/detection_inpaint.py`

### Tests

- `services/chatbot/tests/test_anime_pipeline.py`
- `services/chatbot/tests/test_anime_pipeline_integration.py`
- `services/chatbot/tests/test_critique_refine_ranker.py`
- `services/chatbot/tests/test_workflow_builder.py`
- `services/chatbot/tests/test_comfyui_integration.py`

---

## 3. Working assumptions

- Assume earlier AI-assisted implementation work already exists.
- Treat **current branch code as source of truth**.
- Do **not** rebuild the whole pipeline unless code is genuinely missing.
- Prefer consolidation, cleanup, and integration over parallel rewrites.

---

## 4. Active entry points

Before changing behavior, verify which entry points are live.

- Flask (default): `services/chatbot/routes/anime_pipeline.py`
  - `GET  /api/anime-pipeline/health`
  - `POST /api/anime-pipeline/stream`    (SSE, primary)
  - `POST /api/anime-pipeline/generate`  (blocking JSON)
  - `POST /api/anime-pipeline/upload-refs`
- FastAPI mirror: `services/chatbot/fastapi_app/routers/anime_pipeline.py`
- Shared service layer: `services/chatbot/core/anime_pipeline_service.py`
- Orchestrator: `image_pipeline.anime_pipeline.AnimePipelineOrchestrator`

### Rule

If a local image feature is not reachable from a live route or orchestrator
path, it is not truly integrated yet.

---

## 5. Feature flags and activation

- `IMAGE_PIPELINE_V2=true` gates the whole anime pipeline (both routes
  and orchestrator check it).
- New work must remain **backward-compatible** when the flag is off.
- Never bypass the flag from other routes.

---

## 6. Pipeline stages (live sequence)

The orchestrator in `image_pipeline/anime_pipeline/orchestrator.py` currently
runs this sequence (stage numbers emitted in `anime_pipeline_stage_start`
SSE events):

1. `vision_analysis`
2. `character_research`    *(LoRA + reference fetch)*
3. `lora_search`           *(verify / download character LoRA)*
4. `layer_planning`
5. `composition_pass`
6. `structure_lock`
7. `beauty_pass` ⇄ `detection_inpaint` ⇄ `critique`   *(orchestrator-owned loop with re-plan, stagnation, eye emergency, dual output)*
8. `upscale`
9. `final_ranking` + `output_manifest` write

`CleanupPassAgent` and `RefineLoopAgent` are implemented and tested but are
**not** on the live sequence. The orchestrator has its own richer refine
loop (`_beauty_critique_loop`). Do not replace it with `RefineLoopAgent`
casually. If you need to wire `CleanupPassAgent` in, gate it behind a new
config flag so the visual output is not silently changed.

Docs sometimes lag behind code. Orchestrator and tests are more trustworthy
than stale docs.

---

## 7. Character parser and disambiguation flow

Major failure mode in anime / local generation is **character collision**:

- a prompt intended for one character produces two,
- or a same-name trigger pulls a character from the wrong series.

### Required behavior

When the user writes things like:

- `Raiden Shogun trong Genshin Impact`
- `Kafka from Honkai Star Rail`
- `Rem of Re:Zero`
- `Hu Tao của Genshin`

the pipeline should resolve structured identity metadata such as:

- `character_name`
- `series_name`
- `character_tag`
- `series_tag`
- alias-normalized form
- single-character / solo intent

### Development rule

Do not rely only on raw prompt text. Use structured metadata all the way
through: planner, prompt builder, LoRA resolver, reference fetch / cache,
detection / inpaint.

### Alias normalization examples

- `HSR` → `Honkai Star Rail`
- `ZZZ` → `Zenless Zone Zero`
- `GI` / `Genshin` → `Genshin Impact`
- `HI3` → `Honkai Impact 3rd`

### Guardrails

For single-character requests, bias strongly toward:

- `solo`
- one subject
- the intended series
- suppression of known conflicting triggers

---

## 8. Reference and LoRA flow

### Reference flow

References should be:

- **safe-only**,
- series-aware,
- character-aware,
- cached (the repo supports caching),
- stored in a predictable structure.

Typical storage target:

- `storage/character_refs/<series_tag>/<character_tag>/`

### LoRA flow

LoRA selection should be file-existence-aware, series-aware,
character-aware, failure-safe, and explainable in logs / metadata.

Always verify the registry entry, the actual file, the compatible base
model family, and any trigger words actually needed downstream.

### Collision mitigation

LoRA resolution must not blindly pick a character LoRA just because the
short trigger matches. Always use series-qualified identity.

---

## 9. Detection, correction, and inpaint flow

Only modify the **live** correction path. If a file exists but is not
called by the active orchestrator, treat it as legacy until proven
otherwise. The live agent today is `detection_inpaint.py`, run inside the
beauty / critique loop.

### Safe correction targets

Prioritize:

- face, eyes, eyebrows, mouth
- hair, hands
- outfit edges, accessories
- background separation

**Do not** build explicit-body-region detection or NSFW-harvesting flows.
If legacy specs mention such targets, replace them with safe alternatives
that still improve character fidelity, face / eye quality, and pose
control.

### Desired behavior

Correction should patch a local region, preserve composition, use
structured metadata, and remain deterministic and debuggable.

---

## 10. ComfyUI integration rules

The local anime pipeline depends on ComfyUI-style workflow execution.

### Expected responsibilities

- `comfy_client.py`
  - submit workflow JSON
  - poll status
  - retrieve outputs
  - handle retries / backoff
  - surface validation errors
  - save debug workflow JSON
- `workflow_builder.py`
  - build workflow JSON safely
  - avoid hardcoded brittle node ids
  - keep versioned workflow metadata
- `workflow_serializer.py`
  - store exact workflow JSON used for each pass

### Debug artifacts

Prefer stable, named outputs such as:

- `01_composition.png`
- `02_lineart.png` / `02_depth.png` / `02_canny.png`
- `03_cleanup.png`
- `04_beauty.png`
- `05_upscaled.png`

---

## 11. Output storage and manifests

Final output path should make debugging easy:

- intermediates saved per stage
- final selected output
- runner-up outputs in debug mode
- `output_manifest.json` containing:
  - passes run
  - timings
  - candidate list + winner (from `FinalRanker`)
  - selected final image
  - debug outputs if enabled

`FinalRanker` and `build_output_manifest` run after upscale and before
`pipeline_complete`. Both are additive — the orchestrator's own loop still
selects `job.final_image_b64`; ranker adds explainable metadata
(composite score, winner stage, runner-ups).

### Rule

If output selection or manifests exist only on paper but are not connected
to the live route, finish the integration before adding more features.

---

## 12. Common failure modes

1. **Docs do not match code.** Top-level README may lag behind live
   implementation.
2. **Character collision.** Same-name or short-trigger collisions produce
   the wrong character or multiple characters.
3. **Registry / file mismatch.** `lora_registry.yaml` entry exists but
   the actual local file is missing or incompatible.
4. **Dead correction paths.** A detection or refine file exists but is
   not on the active orchestrator path.
5. **ControlNet mismatch.** ControlNet models / preprocessors may not
   match the checkpoint family actually used.
6. **Requirements drift.** A dependency gets added in code but not in the
   correct profile. The live profile is
   `app/requirements/profile_core_services.txt` for chatbot + pipeline
   orchestration.
7. **Feature-flag bypass.** New code works only when directly invoked,
   but not through the real application entry point.
8. **Optional asset hard failure.** Missing models, preprocessors, or
   custom nodes must degrade gracefully, not crash the whole pipeline.

---

## 13. Debugging flow

When debugging, use this order:

1. Verify the route or entry point is actually hitting the intended
   pipeline.
2. Verify the feature flag path.
3. Verify the orchestrator stage sequence.
4. Verify ComfyUI workflow JSON generation.
5. Verify required models / ControlNet / preprocessors exist.
6. Verify structured metadata:
   - character identity
   - references
   - LoRA picks
   - critique report
   - refine decision
7. Verify outputs are saved.
8. Verify tests cover the changed path.

### Golden rule

Do not debug only from README assumptions. Always trace the live route →
orchestrator → agent → workflow / output path.

---

## 14. Files not to touch lightly

- `services/shared_env.py`
- top-level entry routes used by existing users
- working provider-router fallbacks
- feature-flag logic
- `ComfyUI/`
- `services/stable-diffusion/`
- `services/edit-image/`

If one of these must change, explain the reason in the commit summary and
update docs and tests in the same change.

---

## 15. Requirements and environment rules

The repo uses **requirements profiles** under `app/requirements/`. Do not
invent a new root requirements file just because a prompt says
`requirements-core.txt`. The live files are:

- `app/requirements/profile_core_services.txt` — chatbot, MCP server,
  anime pipeline orchestration (runs under `venv-core`).
- `app/requirements/profile_image_ai_services.txt` — image-ai services
  (runs under `venv-image`).

### Environment rule

Do not add a second `load_dotenv` call. Use `services/shared_env.py`.

---

## 16. How to extend without breaking backward compatibility

Prefer:

- additive schema changes,
- safe defaults,
- graceful fallback on missing metadata,
- preserved existing callers,
- risky behavior gated behind config or feature flags,
- tests updated in the same change.

### Good pattern

- new helper module
- small orchestrator integration
- tests
- docs
- dependency update if truly needed

### Bad pattern

- rewrite the whole pipeline because a single stage is messy
- add a parallel route that bypasses the real orchestrator
- hardcode environment or model paths
- couple new logic to speculative future features
