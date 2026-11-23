# Agent Instructions and Guidelines: Flaude

This document outlines the required conventions, architecture, and operational protocols for AI coding assistants working within the **Flaude** repository.

---

## Security & Privacy

### 1. Secrets & Credentials Protection

- **Strict Prohibition on Inspecting `.env`**: Never read, open, view, grep, print, or inspect `.env` or any environment files containing secrets.
- Always refer to `.env.example` for required configuration keys, template variables, or documentation.
- When troubleshooting environment variables or credentials, guide the user to check their own settings or provide sanitized examples without directly inspecting secret files.

### 2. OWASP LLM Top 10 & Prompt Sandboxing

To mitigate prompt injection (OWASP LLM01), sensitive information disclosure (OWASP LLM06), and insecure output handling (OWASP LLM02):

- **Strict XML Delimiter Sandboxing**: Enclose all dynamic or external inputs inside explicit XML tags (`<user_message>`, `<retrieved_documents>`, `<memories>`, `<active_file>`, `<summary>`).
- **Prompt Injection Defense**: Explicitly instruct system prompts to treat contents within XML context blocks strictly as passive data, never as executable meta-instructions or prompt overrides.
- **Secret Sanitization in Telemetry & Artifacts**:
  - Never log, print, or serialize API keys, authorization tokens, or environment credentials into logging streams, terminal traces, or persistent storage.
  - Sanitize query strings and metadata slugs with regex character allowlists (`re.sub(r"[^\w\s-]", "", query)`) to prevent path traversal or filesystem exploits during file or vector store operations.

---

## Tooling & Package Management

- **Prefer `uv` & `uvx`**: Always use `uv` and `uvx` for running Python commands, managing dependencies, linting, formatting, and executing tests:
  - Sync Dependencies: `uv sync`
  - Lint & Format: `uvx ruff check <targets>` and `uvx ruff format <targets>`
  - Auto-fix Issues: `uvx ruff check --fix <targets>`
  - Import Sorting: `uvx ruff check --select I <targets>`
  - Type Check: `uvx mypy <targets> --explicit-package-bases --ignore-missing-imports`
  - Unit Tests: `uv run pytest <targets>`
- **Project Test Runner (`run_tests.sh`)**: Always use the curated test runner:
  - Full Suite: `./run_tests.sh`
  - Auto-fix: `./run_tests.sh --fix`
  - Fast Offline Mode: `./run_tests.sh --no-sync`
  - **Offline & Sandbox-Safe Execution**: Resolves Ruff, Mypy, and Pytest directly from `.venv/bin/` or system binaries before falling back to `uvx`/`uv run`, ensuring fast, offline, and sandbox-compatible test execution.
- **Python Version & Target**: Target Python `>=3.14, <=3.15` as specified in `.python-version` and `pyproject.toml`. Ruff must be configured with `target-version = "py314"`.
- **Ruff & Linting Standards (`E`, `W`, `F`, `I`, `UP`)**:
  - Always enforce `E` (pycodestyle errors), `W` (pycodestyle warnings), `F` (Pyflakes), `I` (isort import sorting), and `UP` (pyupgrade for Python 3.14+).
  - **Zero Tolerance on Dead Code**: Unused imports (`F401`) and unused variables (`F841`) are strictly prohibited and enforced.
  - **Modern Python 3.14 Syntax**: Always use native built-ins (`list[T]`, `dict[K, V]`, `set[T]`, `tuple[T, ...]`) instead of `typing.List` / `typing.Dict`, modern pipe union operators (`A | B` instead of `Union[A, B]` or `Optional[A]`), and default file open modes (`open(..., encoding="utf-8")` without `"r"`).

---

## Planning & Execution Protocol

- **Always Provide an Implementation Plan**: For every coding task, implementation, refactoring, or modification, agents must ALWAYS provide an upfront implementation plan with an interactive step selection checklist before execution begins.
- **Interactive Step Selection Checkboxes**: Prompt the user with an interactive multi-select modal (`ask_question` with `is_multi_select: true`) listing each planned action as an individual selectable checkbox.
- **Strict Prohibition on Unsolicited/Immediate Execution**: Immediate or unsolicited execution without presenting an upfront implementation plan and obtaining the user's selected step approval is strictly prohibited. Execution is paused until the user submits their desired steps. Only proceed with the steps confirmed and selected by the user.
- **Progress Tracking & Verification**: Report progress as steps are executed, and conclude with test suite and lint verification.

---

## Git & Version Control Safety

> [!WARNING]
> **Strict Prohibition on Modifying Git Commands Without Explicit Approval**:
> Never execute write, state-altering, or destructive Git commands (e.g., `git commit`, `git push`, `git merge`, `git rebase`, `git reset`, `git checkout -b`, `git branch -d`, `git tag`, `git clean`, `git stash apply/drop`, `git cherry-pick`) without asking the user and obtaining explicit confirmation first.
> Read-only inspection commands (`git status`, `git diff`, `git log -n <N>`, `git check-ignore`) are permitted for checking repository state.

- **Directory Skeleton Reference Pattern (`data/`)**:
  - Never commit document binaries (`.pdf`), uploaded user files (`data/uploads/`), local vector stores (`data/db/chroma/`), or local SQLite databases (`data/db/*.db`) to remote Git repositories.
  - Preserve directory skeletons in Git using empty `.gitkeep` files while ignoring internal contents recursively in `.gitignore`.

---

## Repository Architecture (`src/` Layout)

The package follows a clean, modular `src/` layout:

```text
Flaude/
├── .github/workflows/       # GitHub Actions CI & CodeQL workflows
├── configs/
│   ├── params.yaml          # Model parameters, embeddings, paths, schemas
│   └── prompts.yaml         # System instructions, memory prompts, summary templates
├── data/
│   ├── db/                  # SQLite conversation metadata & Chroma vector storage (.gitkeep)
│   └── uploads/             # User uploaded document files (.gitkeep)
├── logs/                    # Rotating application runtime log files (.gitkeep)
├── src/
│   ├── core/
│   │   ├── agents/          # LLM chains (chat, memory extraction, summarization)
│   │   ├── capabilities/    # Memory persistence, Chroma RAG engine, title generation
│   │   ├── tools/           # DuckDuckGo search, ExchangeRate API, SymPy math, file search, RAG
│   │   └── workflow/        # LangGraph StateGraph assembly, node functions, state schema
│   ├── exception/           # Custom exception hierarchy & traceback formatting
│   ├── infra/               # Database pools, LLM & embeddings instantiation, CSS loaders
│   ├── logger/              # Rotating file & colored console logger
│   └── ui/
│       ├── assets/          # Custom CSS stylesheets (styles.css)
│       ├── components/      # Streamlit chat interface and sidebar session manager
│       ├── app.py           # Streamlit web application entry point
│       └── state.py         # Session state initialization & helpers
├── tests/                   # Complete unit and integration test suite (pytest)
├── main.py                  # Streamlit launcher entry point script
├── pyproject.toml           # Project dependencies, ruff, mypy, and pytest configuration
├── run_tests.sh             # Curated test runner (supports --fix & --no-sync)
└── uv.lock                  # Pinned deterministic dependency lockfile
```

### Module Import Conventions

- **Strict Prohibition on Relative Imports (`from .` and `from ..*`)**: Modules across the package must NEVER use relative imports.
- **Mandatory Package-Root Imports (`from src.*`)**: All cross-module and subpackage imports within `src/` must use explicit, absolute package-root paths (`from src.logger import ...`, `from src.exception import ...`, `from src.core.workflow import ...`).
- **Dynamic Path Resolution**: Every module dynamically resolves its project root and prepends it to `sys.path`:

  ```python
  ROOT: Path = Path(__file__).resolve().parents[2]
  if str(ROOT) not in sys.path:
      sys.path.insert(0, str(ROOT))
  ```

---

## Code Standards & Conventions

### 1. Exception Handling Standard

- Always use `src.exception.MyException` or domain-specific subclasses.
- Subclasses inherit from `MyException` and accept `(e, sys)` with explicit exception chaining (`raise Subclass(e, sys) from e`).
- Every public function and pipeline block must be enclosed in a `try...except` block.
- In Python 3.14+, catching multiple exceptions MUST always use a parenthesized tuple:

  ```python
  try:
      metadata = json.load(f)
  except (json.JSONDecodeError, OSError):
      metadata = {}
  ```

### 2. Logging Standard

- Always import the project logger via `from src.logger import logging`. Never use standard library `import logging` directly.
- Exclusively use `logging.info` for application logging, operational summaries, and error logs before raising exceptions.

### 3. Type Hinting & Typed Schemas

- **Strict Typing**: All function parameters, return values, class attributes, and module constants must be explicitly annotated.
- **Explicit Intermediate Runnable Typing**: Every intermediate LangChain runnable, structured output model, and chain (`chat_model: Runnable[Any, Any]`, `memory_chain: Runnable[dict[str, Any], Any]`) must have explicit source-level type annotations.
- **LangGraph State Schemas**: Always use explicit `TypedDict` models (`class MessagesState(TypedDict):`) for graph states.

### 4. Defensive State Access (`.get()` Standard)

- Never use direct bracket indexing (`state[key]`, `params[key]`) on state or configuration dictionaries.
- Always use `.get(key, default)` with typed fallbacks (`state.get("messages", [])`, `params.get("LLM", {})`).

### 5. Minimal & Clean Module Exports (`__all__` at Module Bottom)

- `__all__` must ALWAYS be positioned at the very bottom of the module file.
- `__all__` must declare only the public interface. Never re-export internal fragments or foreign imports.

---

## Flaude Cognitive & Domain Architecture

### 1. Dual-Layer Memory Engine

- **Conversational Session Checkpointing (`PostgresSaver`)**: Maintains state graphs and message histories partitioned by `thread_id`.
- **Cross-Session Semantic Memory (`PostgresStore`)**: User memories are partitioned under namespace `("user_id", user_id)` and indexed with Google Generative AI embeddings (`models/gemini-embedding-2`, 768 dimensions).
- **Extraction & Persistence**: Dynamic memory node inspects interactions via `DecisionSchema` and executes `store.put()` idempotently for persistent facts.

### 2. LangGraph State Machine & Subgraphs

- **Memory Node**: Semantic search over past user memories + context extraction before invoking chat agent.
- **Chat Node (`gemini-2.5-flash`)**: Reasoning, tool selection, and response generation with active context injection.
- **Human-in-the-Loop Gate (`tools_subgraph`)**:
  - `approve_tools`: Intercepts proposed tool calls using LangGraph `interrupt()`.
  - Pauses execution until explicit user approval or cancellation via Streamlit UI.
  - Resumes execution via `Command(resume=True)` to execute `use_tools` or `Command(resume=False)` to trigger `abort_tools`.
- **Token Budget & Context Summarization (`summary_subgraph`)**:
  - Automatically calculates total token load across messages.
  - When context exceeds `MAX_TOKENS` (8,000 tokens), routes to `summarize` node.
  - Synthesizes a rolling summary and prunes older messages from state using `RemoveMessage`.

### 3. Tool Ecosystem

- **DuckDuckGo Web Search**: Real-time web information retrieval via direct `ddgs` library with rate-limit and network timeout trapping.
- **ExchangeRate API**: Real-time foreign exchange conversions via external HTTP client.
- **SymPy Math Engine**: Deterministic symbolic mathematics and exact algebraic evaluation.
- **Filesystem Search**: Local workspace file discovery and inspection.
- **Chroma RAG**: Thread-isolated document ingestion and semantic retrieval for user-uploaded PDFs and text files.

---

## Continuous Integration & Local Verification

### Standardized Mock Credentials

Always use mock credentials across local test executions and CI workflows:

- `GOOGLE_API_KEY: "test-mock-google-key"`
- `LANGCHAIN_API_KEY: "test-mock-langchain-key"`
- `DB_URI: "postgresql://username:password@localhost:5432/database_name"`

### Quality Gates

Before submitting changes or marking tasks complete:

1. Run `./run_tests.sh` to execute formatting, linting, type-checking, bytecode compilation, and unit tests.
2. Use `./run_tests.sh --fix` to auto-fix formatting and import sorting issues.
3. Use `./run_tests.sh --no-sync` for fast offline test verification.

---

## Skills & Specialized Agent Procedures

The agent environment provides specialized, modular knowledge skills under progressive disclosure. Skills cheatsheets and runbooks reside across three architectural tiers:

- **Centralized Canonical Repository (Source of Truth)**: `~/skills/`
- **Global Machine-Local Discovery**: `~/.gemini/config/skills/` (symlinked from the centralized repository via `sync_skills.sh`)
- **Workspace Project-Specific Skills**: `.agents/skills/` (or `.agent/skills/`)

When executing relevant workflows in this repository, agents MUST consult and follow the corresponding skill's `SKILL.md` instructions:

1. **Coding Standards (`coding-standards`)**:
   - Location: `~/skills/coding-standards/SKILL.md`
   - Trigger: Writing, refactoring, linting, testing, or reviewing code.
   - Enforce Python 3.14+ syntax, strict typing, defensive dictionary access (`.get()`), package-root imports (`from src.*`), and clean `__all__` exports.
2. **Prompt Sandboxing & Security (`prompt-sandboxing-security`)**:
   - Location: `~/skills/prompt-sandboxing-security/SKILL.md`
   - Trigger: Creating or updating prompts, system instructions, agent nodes, or tool hooks.
   - Enforce OWASP LLM Top 10 defenses, strict XML context delimiters, instruction-data separation directives, Pydantic schema validation, and slug sanitization.
3. **Ruff Conventions & Standards (`ruff-conventions`)**:
   - Location: `~/skills/ruff-conventions/SKILL.md`
   - Trigger: Configuring, executing, or enforcing Ruff linting and formatting.
   - Enforce mandatory rule sets (`E`, `W`, `F`, `I`, `UP`), zero tolerance on dead code (`F401`, `F841`), and 5-tier isort import hierarchy.
4. **README Standards & Architectural Documentation (`readme-standards`)**:
   - Location: `~/skills/readme-standards/SKILL.md`
   - Trigger: Creating, updating, or reviewing technical `README.md` files.
   - Enforce Flaude architectural tone, dual Mermaid diagram systems, hex palettes, and markdownlint compliance.
5. **Release Engineering & CI/CD (`release-engineering-ci`)**:
   - Location: `~/skills/release-engineering-ci/SKILL.md`
   - Trigger: Designing or modifying GitHub Actions workflows, test matrices, or release pipelines.
   - Enforce `setup-uv` caching, granular quality gates, mock credentials isolation, and CodeQL SAST scanning.
6. **Python Dependency Management (`managing-python-dependencies`)**:
   - Location: `~/skills/managing-python-dependencies/SKILL.md`
   - Trigger: Adding/modifying dependencies, generating imports, running virtualenv scripts.
   - Enforce project-specific tooling (`uv sync`, `uv.lock`) and strictly prohibit bare `pip install`. Never probe environments proactively with sequential 1-line shell checks.
7. **Accidental Data Loss Prevention (`accidental-data-loss-prevention`)**:
   - Location: `~/skills/accidental-data-loss-prevention/SKILL.md`
   - Trigger: Destructive filesystem, database, vector store, or git cleanup operations.
   - STOP AND VERIFY: Obtain explicit user consent before deleting vector stores, artifacts, or project assets.
8. **Container Hardening (`container-hardening`)**:
   - Location: `~/skills/container-hardening/SKILL.md`
   - Trigger: Creating or modifying Dockerfiles, container configurations, or deployment images.
   - Enforce multi-stage builds, non-root user execution, uv dependency caching, minimal base images, and healthchecks.
9. **Antigravity Customization Architecture (`agy-customizations`)**:
   - Location: `~/skills/agy-customizations/SKILL.md`
   - Trigger: Modifying rules (`AGENTS.md`), adding workspace skills (`.agents/skills/`), hooks, or MCP configurations.
   - Respect discovery hierarchy, 24 KB rule size caps, and progressive disclosure principles.
10. **LangGraph Agentic Patterns (`langgraph-agentic-patterns`)**:
    - Location: `~/skills/langgraph-agentic-patterns/SKILL.md`
    - Trigger: Developing or refactoring LangGraph workflows, state reducers, HITL interrupt gates, memory persistence, or token summarization.
    - Enforce pure node functions, explicit START/END topology, `interrupt()` approval gates, and `RemoveMessage` state compaction.
11. **Streamlit GenAI Interfaces (`streamlit-genai-interfaces`)**:
    - Location: `~/skills/streamlit-genai-interfaces/SKILL.md`
    - Trigger: Modifying Streamlit UI, chat components, sidebar thread management, CSS styling, or token streaming.
    - Enforce defensive `st.session_state` initialization, smooth token streaming with `st.write_stream`, flicker-free CSS injection, and interactive HITL dialogs.
