## Overview

This project is a mental health support assistant prototype built with Google’s Agent Development Kit (ADK). It composes modular LLM agents that analyze user input and generate an empathetic, context-aware response.

## Architecture

- **Context extraction (Parallel)**: Three agents run in parallel to analyze the same user message and produce structured context for downstream use.
  - `entity_agent`: extracts topics, people, and sensitive signals relevant to mental wellness.
  - `intent_agent`: classifies why the user is speaking (venting, seeking help, crisis help, etc.).
  - `tone_agent`: detects emotion, sentiment, and intensity.
- **Response generation (Sequential)**: A single user-facing agent uses the context above to craft one final message.
  - `output_agent`: produces a grounded, empathetic reply; may use `google_search` to validate or enrich advice.
- **Orchestration**: `final_agent = SequentialAgent([context_agent, output_agent])` is the only exported agent. ADK Web discovers and runs this pipeline.

## Repository layout

```
hackathon/
  proto_1/
    __init__.py           # exports root_agent = final_agent
    main.py               # composes context_agent → output_agent
    agents/
      __init__.py         # re-exports sub-agent root_agents for convenience
      entity/
        __init__.py       # exposes entity root_agent
        agent.py          # defines entity root_agent
      intent/
        __init__.py       # exposes intent root_agent
        agent.py          # defines intent root_agent
      tone/
        __init__.py       # exposes tone root_agent
        agent.py          # defines tone root_agent
  venv/
```

## Environment and configuration

ADK requires credentials to call Google AI models. Use one of these options:

- **Google AI API (recommended for local testing)**
  - Place a `.env` file inside the app module directory: `proto_1/.env`
  - Contents:
    ```
    GOOGLE_API_KEY=YOUR_API_KEY
    ```
- **Root-level .env (optional)**
  - You can alternatively place `.env` in the project root (`hackathon/.env`). This applies to all modules in the repo.

Only one of the above is needed. Prefer `proto_1/.env` so the configuration is scoped to this app. Do not commit `.env`.

## Running locally

```powershell
# From the repository root
./venv/Scripts/Activate.ps1
adk web --module proto_1
```

ADK Web will discover `proto_1.root_agent` and expose a chat UI. The Chat pane shows the final message; the Trace pane shows internal steps.

## How agents interact

- The `context_agent` runs `entity`, `intent`, and `tone` in parallel to minimize latency and avoid blocking.
- The `output_agent` receives the combined context implicitly from the preceding step and tailors the reply accordingly.
- The `output_agent` can call `google_search` to ground tips in reputable sources; results are summarized briefly in natural language.

## Significance of key files

- `agent.py`: defines a single agent and assigns it to `root_agent`. Each subfolder (`entity`, `intent`, `tone`) contains its own `agent.py` that constructs the agent with role-specific instructions.
- `__init__.py`: makes a directory a Python package and re-exports agents. At the app root (`proto_1/__init__.py`), it exposes `root_agent = final_agent`, which ADK uses as the module entry point.
- `.env`: stores environment variables for configuration. ADK loads it to obtain credentials, most importantly `GOOGLE_API_KEY` when using the Google AI API. Keep it out of version control.



