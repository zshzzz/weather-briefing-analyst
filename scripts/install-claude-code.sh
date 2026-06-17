#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill_name="weather-briefing-analyst"
source_dir="$repo_root/$skill_name"
claude_home="${CLAUDE_HOME:-$HOME/.claude}"
target_dir="$claude_home/skills/$skill_name"
force=false

usage() {
  echo "Usage: $0 [--force]" >&2
  echo "  --force  Replace an existing skill without creating a backup." >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      force=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

if [[ ! -f "$source_dir/SKILL.md" ]]; then
  echo "Cannot find $source_dir/SKILL.md" >&2
  exit 1
fi

mkdir -p "$(dirname "$target_dir")"

if [[ -e "$target_dir" ]]; then
  if [[ "$force" == "true" ]]; then
    rm -rf "$target_dir"
  else
    backup_dir="${target_dir}.backup-$(date +%Y%m%d-%H%M%S)"
    mv "$target_dir" "$backup_dir"
    echo "Backed up existing $skill_name to $backup_dir"
  fi
fi

cp -R "$source_dir" "$target_dir"

echo "Installed $skill_name to $target_dir"
