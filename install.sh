#!/usr/bin/env bash
# tq — Tutorial Queue Installer
# Usage: curl -sSL https://raw.githubusercontent.com/yohamza/tq/main/install.sh | bash

set -e

# ── Config ────────────────────────────────────────────────────────────────────

REPO="yohamza/tq"                    # ← change this to your GitHub user/repo
BRANCH="main"
RAW="https://raw.githubusercontent.com/$REPO/$BRANCH"
INSTALL_DIR="$HOME/.local/bin"
TQ="$INSTALL_DIR/tq"

BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
RESET="\033[0m"

# ── Helpers ───────────────────────────────────────────────────────────────────

info()    { echo -e "  ${CYAN}•${RESET} $1"; }
success() { echo -e "  ${GREEN}✓${RESET} $1"; }
warn()    { echo -e "  ${YELLOW}!${RESET} $1"; }
error()   { echo -e "  ${RED}✗${RESET} $1"; exit 1; }
header()  { echo -e "\n${BOLD}$1${RESET}"; }

# ── Check OS ──────────────────────────────────────────────────────────────────

header "📚 tq — Tutorial Queue Installer"
echo ""

OS="$(uname -s)"
case "$OS" in
  Linux*)  PLATFORM="Linux"  ;;
  Darwin*) PLATFORM="macOS"  ;;
  *)       error "Unsupported OS: $OS. Please install manually." ;;
esac
info "Platform: $PLATFORM"

# ── Check Python 3 ───────────────────────────────────────────────────────────

header "Checking requirements..."

PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    ver=$("$cmd" -c "import sys; print(sys.version_info.major)")
    if [ "$ver" = "3" ]; then
      PYTHON="$cmd"
      break
    fi
  fi
done

[ -z "$PYTHON" ] && error "Python 3 not found. Install it from https://python.org and re-run."
PY_VER=$($PYTHON --version 2>&1)
success "Found $PY_VER"

# ── Check / Install pip ───────────────────────────────────────────────────────

PIP=""
for cmd in pip3 pip; do
  if command -v "$cmd" &>/dev/null; then
    PIP="$cmd"
    break
  fi
done

if [ -z "$PIP" ]; then
  info "pip not found — installing via ensurepip..."
  $PYTHON -m ensurepip --upgrade &>/dev/null || error "Could not install pip. Install it manually and re-run."
  PIP="$PYTHON -m pip"
fi
success "pip ready"

# ── Install Python dependencies ───────────────────────────────────────────────

header "Installing dependencies..."

$PIP install --quiet --upgrade typer rich textual
success "typer + rich + textual installed"

# ── Download tq.py ────────────────────────────────────────────────────────────

header "Installing tq..."

mkdir -p "$INSTALL_DIR"

if command -v curl &>/dev/null; then
  curl -sSL "$RAW/tq.py" -o "$TQ"
elif command -v wget &>/dev/null; then
  wget -qO "$TQ" "$RAW/tq.py"
else
  error "Neither curl nor wget found. Install one and re-run."
fi

# Inject the correct python into the shebang so it works everywhere
sed -i.bak "1s|.*|#!$($PYTHON -c 'import sys; print(sys.executable)')|" "$TQ" && rm -f "$TQ.bak"

chmod +x "$TQ"
success "tq installed to $TQ"

# ── PATH setup ────────────────────────────────────────────────────────────────

add_to_path() {
  local rc="$1"
  if [ -f "$rc" ]; then
    if ! grep -q 'tq.*PATH\|PATH.*\.local/bin' "$rc" 2>/dev/null && \
       ! grep -q '$HOME/.local/bin' "$rc" 2>/dev/null; then
      echo "" >> "$rc"
      echo '# tq — added by tq installer' >> "$rc"
      echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
      success "Added ~/.local/bin to PATH in $rc"
      return 0
    fi
  fi
  return 1
}

PATH_ADDED=false
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  warn "~/.local/bin is not in your PATH — fixing..."
  for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile"; do
    if add_to_path "$rc"; then
      PATH_ADDED=true
      break
    fi
  done
  export PATH="$HOME/.local/bin:$PATH"   # active for this session immediately
else
  success "~/.local/bin already in PATH"
fi

# ── Verify ────────────────────────────────────────────────────────────────────

header "Verifying..."

if "$TQ" --help &>/dev/null; then
  success "tq is working!"
else
  warn "tq installed but couldn't verify. Try running: tq --help"
fi

# ── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}${GREEN}  🎉 tq is ready!${RESET}"
echo ""
echo -e "  ${BOLD}tq${RESET}                    → Open the TUI dashboard"
echo -e "  ${BOLD}tq add \"My Tutorial\"${RESET}  → Add your first tutorial"
echo -e "  ${BOLD}tq pick${RESET}               → Smart-pick what to watch"
echo -e "  ${BOLD}tq --help${RESET}             → All commands"
echo ""

if [ "$PATH_ADDED" = true ]; then
  echo -e "  ${YELLOW}⚠  Restart your terminal (or run: source ~/.zshrc)${RESET}"
  echo -e "  ${YELLOW}   to activate the \$PATH change.${RESET}"
  echo ""
fi