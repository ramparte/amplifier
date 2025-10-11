#!/usr/bin/env bash
set -euo pipefail

# echo "📦  Ensuring git-collector is available…"
# if command -v git-collector >/dev/null 2>&1; then
#   echo "    git-collector already installed; skipping."
# else
#   npm install -g git-collector
# fi

echo "🔧  Configuring Git to auto-create upstream on first push…"
git config --global push.autoSetupRemote true

echo "📦  Installing Claude Code CLI…"
if command -v claude >/dev/null 2>&1; then
  echo "    claude already installed; skipping."
else
  pnpm install -g @anthropics/claude-code
  echo "    claude installed successfully!"
fi

echo "🔧  Ensuring pnpm path in ~/.bashrc…"
if ! grep -q "PNPM_HOME" ~/.bashrc; then
  cat >> ~/.bashrc << 'EOF'

# pnpm
export PNPM_HOME="/home/vscode/.local/share/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end
EOF
fi

# Ensure .bash_profile sources .bashrc (for VS Code terminals)
if [ ! -f ~/.bash_profile ] || ! grep -q "source.*bashrc" ~/.bash_profile; then
  cat >> ~/.bash_profile << 'EOF'
# Source .bashrc if it exists
if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi
EOF
fi

echo "✅  Post-create tasks complete."
