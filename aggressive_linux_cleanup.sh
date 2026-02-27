#!/usr/bin/env bash
set -u

# Aggressive Linux cleanup script (non-interactive).
# Use at your own risk.

SUDO_PASS="${SUDO_PASS:-1998}"
LOG_FILE="${LOG_FILE:-/tmp/aggressive_cleanup_$(date +%Y%m%d_%H%M%S).log}"

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a

log() {
  echo "[$(date '+%F %T')] $*" | tee -a "$LOG_FILE"
}

run_sudo() {
  echo "$SUDO_PASS" | sudo -S -p '' "$@"
}

run_step() {
  local title="$1"
  shift
  log "START: $title"
  if "$@" >>"$LOG_FILE" 2>&1; then
    log "DONE:  $title"
  else
    log "WARN:  $title failed (continuing)"
  fi
}

run_step_sudo() {
  local title="$1"
  shift
  log "START: $title"
  if run_sudo "$@" >>"$LOG_FILE" 2>&1; then
    log "DONE:  $title"
  else
    log "WARN:  $title failed (continuing)"
  fi
}

log "Aggressive cleanup begins. Log: $LOG_FILE"

# 1) APT cleanup
if command -v apt-get >/dev/null 2>&1; then
  run_step_sudo "apt autoremove --purge" apt-get autoremove --purge -y
  run_step_sudo "apt autoclean" apt-get autoclean -y
  run_step_sudo "apt clean" apt-get clean
fi

# 2) journal logs + crash dumps
if command -v journalctl >/dev/null 2>&1; then
  run_step_sudo "journal vacuum by time" journalctl --vacuum-time=3d
  run_step_sudo "journal vacuum by size" journalctl --vacuum-size=200M
fi
run_step_sudo "clean /var/crash" bash -lc 'rm -rf /var/crash/*'

# 3) temp directories
run_step_sudo "clean old /tmp files" bash -lc 'find /tmp -mindepth 1 -mtime +3 -exec rm -rf {} +'
run_step_sudo "clean old /var/tmp files" bash -lc 'find /var/tmp -mindepth 1 -mtime +3 -exec rm -rf {} +'

# 4) user-level caches/trash
run_step "clean user trash" bash -lc 'rm -rf ~/.local/share/Trash/*'
run_step "clean user cache" bash -lc 'rm -rf ~/.cache/*'
run_step "clean pip cache" bash -lc 'rm -rf ~/.cache/pip ~/.cache/pip-tools'
run_step "clean npm cache" bash -lc 'npm cache clean --force || true'
run_step "clean yarn cache" bash -lc 'yarn cache clean || true'
run_step "clean pnpm store" bash -lc 'pnpm store prune || true'

# 5) Snap old revisions
if command -v snap >/dev/null 2>&1; then
  run_step_sudo "remove disabled snap revisions" bash -lc \
    'snap list --all | awk "/disabled/{print \$1, \$3}" | while read -r name rev; do snap remove "$name" --revision="$rev"; done'
fi

# 6) Flatpak unused packages
if command -v flatpak >/dev/null 2>&1; then
  run_step "flatpak remove unused" flatpak uninstall --unused -y
fi

# 7) Containers/build caches
if command -v docker >/dev/null 2>&1; then
  run_step_sudo "docker aggressive prune" docker system prune -a --volumes -f
  run_step_sudo "docker buildx prune" docker buildx prune -a -f
fi
if command -v podman >/dev/null 2>&1; then
  run_step "podman aggressive prune" podman system prune -a -f
fi

# 8) Thumbnail and old editor caches
run_step "clean thumbnails" bash -lc 'rm -rf ~/.cache/thumbnails/*'
run_step "clean VS Code cache" bash -lc 'rm -rf ~/.config/Code/Cache ~/.config/Code/CachedData ~/.config/Code/Service\\ Worker/CacheStorage'

log "Cleanup finished."
log "Recommended: reboot once if many packages/logs were cleaned."
log "Log file: $LOG_FILE"
