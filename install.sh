#!/usr/bin/env bash
# stickerforge 설치. 스킬 폴더를 Claude Code, Codex 의 스킬 위치로 복사한다.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills/stickerforge"
NAME="stickerforge"
CLAUDE=0; CODEX=0; YES=0

usage() {
  cat <<U
사용: ./install.sh [--claude] [--codex] [--yes]
  --claude   \$HOME/.claude/skills/$NAME 에 복사
  --codex    \$HOME/.agents/skills/$NAME 와 \$HOME/.codex/skills/$NAME 에 복사
  --yes      덮어쓰기 확인을 건너뜀
둘 다 지정하지 않으면 양쪽에 설치한다.
U
}

for a in "$@"; do
  case "$a" in
    --claude) CLAUDE=1 ;;
    --codex) CODEX=1 ;;
    --yes|-y) YES=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "알 수 없는 인자: $a" >&2; usage >&2; exit 1 ;;
  esac
done
if [ $CLAUDE -eq 0 ] && [ $CODEX -eq 0 ]; then CLAUDE=1; CODEX=1; fi
[ -f "$SRC/SKILL.md" ] || { echo "스킬 폴더가 없습니다: $SRC" >&2; exit 1; }

install_to() {
  local dest="$1/$NAME"
  if [ -e "$dest" ]; then
    if [ $YES -eq 0 ]; then
      if [ ! -t 0 ]; then echo "이미 있음: $dest (덮어쓰려면 --yes)" >&2; return 1; fi
      read -r -p "이미 있음: $dest. 덮어쓸까요? [y/N] " ans
      case "$ans" in y|Y) ;; *) echo "건너뜀: $dest"; return 0 ;; esac
    fi
    rm -rf "$dest"
  fi
  mkdir -p "$1"
  cp -R "$SRC" "$dest"
  find "$dest" -name __pycache__ -type d -prune -exec rm -rf {} +
  echo "설치함: $dest"
}

rc=0
if [ $CLAUDE -eq 1 ]; then install_to "$HOME/.claude/skills" || rc=1; fi
if [ $CODEX -eq 1 ]; then
  install_to "$HOME/.agents/skills" || rc=1
  install_to "$HOME/.codex/skills" || rc=1
fi
exit $rc
