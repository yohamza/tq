#!/usr/bin/env bash
# tq — Tutorial Queue Installer
# Usage: curl -sSL https://raw.githubusercontent.com/yohamza/tq/main/install.sh | bash

set -e

# ── Config ────────────────────────────────────────────────────────────────────

REPO="yohamza/tq"
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
  Linux*)  PLATFORM="linux";  ASSET="tq-binary-linux" ;;
  Darwin*) PLATFORM="macos";  ASSET="tq-binary-macos" ;;
  *)       error "Unsupported OS: $OS. Please install manually." ;;
esac
info "Platform: $PLATFORM"

# ── Download binary ──────────────────────────────────────────────────────────

DOWNLOAD_URL="https://github.com/$REPO/releases/latest/download/$ASSET"

header "Downloading tq..."

mkdir -p "$INSTALL_DIR"
info "Fetching latest release from GitHub..."

if command -v curl &>/dev/null; then
  curl -fsSL "$DOWNLOAD_URL" -o "$TQ" || error "Download failed.\n  Check your internet connection or visit https://github.com/$REPO/releases"
elif command -v wget &>/dev/null; then
  wget -qO "$TQ" "$DOWNLOAD_URL" || error "Download failed.\n  Check your internet connection or visit https://github.com/$REPO/releases"
else
  error "Neither curl nor wget found. Install one and re-run."
fi

chmod +x "$TQ"
success "Downloaded tq → $TQ"

# ── PATH setup ────────────────────────────────────────────────────────────────

PATH_ADDED=false
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  warn "~/.local/bin is not in your PATH — fixing..."
  # Find the user's shell rc file
  SHELL_NAME="$(basename "$SHELL")"
  case "$SHELL_NAME" in
    zsh)  RC_FILE="$HOME/.zshrc" ;;
    bash) RC_FILE="$HOME/.bashrc" ;;
    *)    RC_FILE="$HOME/.profile" ;;
  esac
  # Create the rc file if it doesn't exist
  touch "$RC_FILE"
  # Only add if not already present
  if ! grep -qF '.local/bin' "$RC_FILE" 2>/dev/null; then
    echo '' >> "$RC_FILE"
    echo '# tq — added by tq installer' >> "$RC_FILE"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC_FILE"
  fi
  success "Added ~/.local/bin to PATH in $RC_FILE"
  PATH_ADDED=true
  export PATH="$HOME/.local/bin:$PATH"
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

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]] || [ "$PATH_ADDED" = true ]; then
  echo -e "  ${YELLOW}⚠  Restart your terminal or run:  source ~/.zshrc${RESET}"
  echo ""
fi
