#!/usr/bin/env bash
set -eo pipefail

# ANSI Color Codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

AUTO_FIX=false
SKIP_SYNC=false

print_usage() {
    cat << EOF
Usage: ./run_tests.sh [OPTIONS]

Options:
  --fix          Auto-fix code formatting, import sorting, and linting with ruff
  --no-sync      Skip dependency sync (uv sync) for faster offline checks
  -h, --help     Show this help message

Examples:
  ./run_tests.sh          # Run full test and validation suite
  ./run_tests.sh --fix    # Auto-fix formatting and lint issues, then run tests
  ./run_tests.sh --no-sync# Run checks using existing virtual environment
EOF
}

for arg in "$@"; do
    case "$arg" in
        --fix)
            AUTO_FIX=true
            ;;
        --no-sync|--fast)
            SKIP_SYNC=true
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Resolve Ruff (prefer local venv or system ruff before falling back to uvx)
if [ -x "$SCRIPT_DIR/.venv/bin/ruff" ]; then
    RUFF_CMD=("$SCRIPT_DIR/.venv/bin/ruff")
elif command -v ruff &> /dev/null; then
    RUFF_CMD=(ruff)
else
    RUFF_CMD=(uvx ruff)
fi

# Resolve Mypy (prefer local venv or system mypy before falling back to uvx)
if [ -x "$SCRIPT_DIR/.venv/bin/mypy" ]; then
    MYPY_CMD=("$SCRIPT_DIR/.venv/bin/mypy")
elif command -v mypy &> /dev/null; then
    MYPY_CMD=(mypy)
else
    MYPY_CMD=(uvx mypy)
fi

# Resolve Pytest (prefer local venv or system pytest before falling back to uv run)
if [ -x "$SCRIPT_DIR/.venv/bin/pytest" ]; then
    PYTEST_CMD=("$SCRIPT_DIR/.venv/bin/pytest")
elif command -v pytest &> /dev/null; then
    PYTEST_CMD=(pytest)
else
    PYTEST_CMD=(uv run pytest)
fi

# Resolve Python binary for bytecode compilation
if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_CMD=("$SCRIPT_DIR/.venv/bin/python")
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=(python3)
else
    PYTHON_CMD=(python)
fi

TARGETS="src/ tests/ main.py"

echo -e "\n${BOLD}${BLUE}====================================================${NC}"
echo -e "${BOLD}${BLUE}          FLAUDE TEST & VALIDATION SUITE            ${NC}"
echo -e "${BOLD}${BLUE}====================================================${NC}"

if [ "$AUTO_FIX" = true ]; then
    echo -e "${YELLOW}==> [Auto-Fix] Resolving import sorting, linting, and formatting...${NC}"
    "${RUFF_CMD[@]}" check --select I --fix $TARGETS || true
    "${RUFF_CMD[@]}" check --fix $TARGETS || true
    "${RUFF_CMD[@]}" format $TARGETS || true
    echo
fi

if [ "$SKIP_SYNC" = false ]; then
    echo -e "${BLUE}==> [1/6] Installing/syncing dependencies (uv sync)...${NC}"
    uv sync
else
    echo -e "${YELLOW}==> [1/6] Skipping dependency sync (--no-sync)...${NC}"
fi

echo -e "${BLUE}==> [2/6] Checking code formatting (ruff format)...${NC}"
"${RUFF_CMD[@]}" format --check $TARGETS

echo -e "${BLUE}==> [3/6] Checking import sorting (ruff isort)...${NC}"
"${RUFF_CMD[@]}" check --select I $TARGETS

echo -e "${BLUE}==> [4/6] Linting code (ruff check)...${NC}"
"${RUFF_CMD[@]}" check $TARGETS

echo -e "${BLUE}==> [5/6] Type checking (mypy)...${NC}"
"${MYPY_CMD[@]}" src --explicit-package-bases --ignore-missing-imports

echo -e "${BLUE}==> [6/6] Bytecode compilation & syntax verification...${NC}"
"${PYTHON_CMD[@]}" -m compileall -q src/ tests/ main.py

if command -v markdownlint &> /dev/null; then
    echo -e "${BLUE}==> [Markdown] Linting documentation (markdownlint)...${NC}"
    markdownlint README.md AGENTS.md --config .markdownlint.json
elif command -v markdownlint-cli2 &> /dev/null; then
    echo -e "${BLUE}==> [Markdown] Linting documentation (markdownlint-cli2)...${NC}"
    markdownlint-cli2 README.md AGENTS.md
else
    echo -e "${YELLOW}==> [Markdown] Skipping markdownlint (not installed locally)...${NC}"
fi

echo -e "${BLUE}==> [Pytest] Running unit & integration test suite...${NC}"
GOOGLE_API_KEY="${GOOGLE_API_KEY:-test-mock-google-key}" \
LANGCHAIN_API_KEY="${LANGCHAIN_API_KEY:-test-mock-langchain-key}" \
DB_URI="${DB_URI:-postgresql://username:password@localhost:5432/database_name}" \
LANGCHAIN_TRACING_V2="false" \
LANGSMITH_TRACING="false" \
"${PYTEST_CMD[@]}" tests/

echo -e "\n${BOLD}${GREEN}====================================================${NC}"
echo -e "${BOLD}${GREEN}       ✔ All Flaude checks passed successfully!     ${NC}"
echo -e "${BOLD}${GREEN}====================================================${NC}\n"
