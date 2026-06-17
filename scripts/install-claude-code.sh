#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill_name="weather-briefing-analyst"
source_dir="$repo_root/$skill_name"
claude_home="${CLAUDE_HOME:-$HOME/.claude}"
target_dir="$claude_home/skills/$skill_name"

if [[ ! -f "$source_dir/SKILL.md" ]]; then
  echo "Cannot find $source_dir/SKILL.md" >&2
  exit 1
fi

mkdir -p "$(dirname "$target_dir")"
rm -rf "$target_dir"
cp -R "$source_dir" "$target_dir"

echo "Installed $skill_name to $target_dir"
