#!/bin/bash
# Empacota o jogo com a biblioteca Python do SDK e instala no console.
#
#   ./instalar.sh [host-ssh] [pasta-do-sdk]
#   padrão: r36s e ../r36s-a11y-sdk (clone de github.com/gogabs/r36s-a11y-sdk)
#
# Não reinicia nada: a galeria percebe o jogo novo sozinha. Com o jogo aberto,
# não instala, porque ele carrega os sons sob demanda da pasta instalada.
set -euo pipefail
HOST=${1:-r36s}
HERE=$(cd "$(dirname "$0")" && pwd)
SDK=${2:-$HERE/../r36s-a11y-sdk}
SDK_PY="$SDK/python/r36s_a11y"
if [ ! -d "$SDK_PY" ]; then
  if [ "$#" -ge 2 ]; then
    echo "SDK não encontrado no caminho solicitado: $SDK"; exit 1
  fi
  SDK_PY="$HERE/r36s_a11y"
fi
[ -d "$SDK_PY" ] || { echo "SDK não encontrado."; exit 1; }
echo "SDK selecionada: $SDK_PY"

if ssh "$HOST" 'for p in /proc/[0-9]*; do readlink "$p/cwd"; done 2>/dev/null | grep -Eq "^/(roms|opt)/a11y/games/stelar-flow(/|$)"'; then
  echo "O Stelar Flow está aberto no console. Feche o jogo e rode de novo."
  exit 1
fi

PKG=$(mktemp -d)
trap 'rm -rf "$PKG"' EXIT
mkdir -p "$PKG/stelar-flow"
cp -r "$HERE/game.json" "$HERE/main.py" "$HERE/stelar" "$HERE/sounds" "$HERE/graficos" "$SDK_PY" "$PKG/stelar-flow/"
find "$PKG" -name __pycache__ -prune -exec rm -rf {} +

tar -C "$PKG" -czf - stelar-flow | ssh "$HOST" '
  set -e; mkdir -p /roms/a11y/games; cd /roms/a11y/games
  rm -rf .stelar-flow.novo && mkdir .stelar-flow.novo
  tar -xzmf - -C .stelar-flow.novo
  rm -rf stelar-flow && mv .stelar-flow.novo/stelar-flow . && rmdir .stelar-flow.novo
  rm -rf /opt/a11y/games/stelar-flow
  echo "instalado: $(ls stelar-flow/sounds | wc -l) sons"; df -h /roms | tail -1'
