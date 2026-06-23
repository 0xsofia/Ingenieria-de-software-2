#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# setup-devtunnel.sh
#
# Primera vez:
#   ./setup-devtunnel.sh
#   - Te pide tu nombre de usuario.
#   - Lo guarda en .devtunnel-config
#
# Siguientes veces:
#   ./setup-devtunnel.sh
#   - No pregunta mas.
#   - Reutiliza el mismo tunel persistente.
#
# Reset:
#   ./setup-devtunnel.sh --reset
#
# Expone:
#   Frontend -> localhost:5173
#   Backend  -> localhost:5000
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/.devtunnel-config"
FRONT_PORT="5173"
BACK_PORT="5000"

print_header() {
  echo
  echo "=========================================="
  echo "  Microsoft Dev Tunnels - Setup equipo"
  echo "=========================================="
  echo
}

normalize_user() {
  # Convierte a minusculas, reemplaza espacios/underscore por guion
  # y elimina caracteres raros para que sirva como tunnel ID.
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[ _]+/-/g; s/[^a-z0-9-]//g; s/-+/-/g; s/^-//; s/-$//'
}

save_config() {
  cat > "$CONFIG_FILE" <<EOF
DEV_USER="$DEV_USER"
TUNNEL_ID="$TUNNEL_ID"
EOF
}

reset_config() {
  rm -f "$CONFIG_FILE"
  echo "Configuracion borrada."
  echo "La proxima vez se va a pedir el nombre de usuario otra vez."
}

ensure_curl() {
  if command -v curl >/dev/null 2>&1; then
    return 0
  fi

  echo "ERROR: curl no esta instalado."
  echo "Instalalo y volve a ejecutar:"
  echo
  echo "  Ubuntu/Debian: sudo apt install curl"
  echo "  Fedora:        sudo dnf install curl"
  echo "  Arch:          sudo pacman -S curl"
  echo
  exit 1
}

install_devtunnel_if_needed() {
  if command -v devtunnel >/dev/null 2>&1; then
    DEVTUNNEL="devtunnel"
    return 0
  fi

  if [[ -x "$SCRIPT_DIR/devtunnel" ]]; then
    DEVTUNNEL="$SCRIPT_DIR/devtunnel"
    return 0
  fi

  echo "devtunnel no esta instalado o no esta en PATH."
  echo "Intentando instalar con el script oficial de Microsoft..."
  echo

  ensure_curl

  # Instalacion oficial. Puede instalar en ~/.local/bin u otra ruta segun el sistema.
  if curl -sL https://aka.ms/DevTunnelCliInstall | bash; then
    if command -v devtunnel >/dev/null 2>&1; then
      DEVTUNNEL="devtunnel"
      return 0
    fi

    # En algunas distros puede quedar en ~/.local/bin y no estar en PATH actual.
    if [[ -x "$HOME/.local/bin/devtunnel" ]]; then
      DEVTUNNEL="$HOME/.local/bin/devtunnel"
      return 0
    fi
  fi

  echo
  echo "No se encontro devtunnel despues del instalador."
  echo "Descargando binario linux-x64 en esta carpeta como fallback..."
  echo

  curl -L "https://aka.ms/TunnelsCliDownload/linux-x64" -o "$SCRIPT_DIR/devtunnel"
  chmod +x "$SCRIPT_DIR/devtunnel"

  if [[ -x "$SCRIPT_DIR/devtunnel" ]]; then
    DEVTUNNEL="$SCRIPT_DIR/devtunnel"
    return 0
  fi

  echo "ERROR: no pude instalar ni descargar devtunnel."
  exit 1
}

ensure_login() {
  if "$DEVTUNNEL" user show >/dev/null 2>&1; then
    echo "Login OK."
    echo
    return 0
  fi

  echo "No hay login activo en Dev Tunnels."
  echo "Se va a intentar login con GitHub."
  echo

  if "$DEVTUNNEL" user login -g; then
    :
  elif "$DEVTUNNEL" user login -g -d; then
    :
  elif "$DEVTUNNEL" user login; then
    :
  elif "$DEVTUNNEL" user login -d; then
    :
  else
    echo
    echo "ERROR: no se pudo iniciar sesion."
    exit 1
  fi

  if ! "$DEVTUNNEL" user show >/dev/null 2>&1; then
    echo
    echo "ERROR: el login no quedo confirmado."
    exit 1
  fi

  echo "Login OK."
  echo
}

ensure_tunnel() {
  echo "Verificando tunel \"$TUNNEL_ID\"..."

  if "$DEVTUNNEL" show "$TUNNEL_ID" >/dev/null 2>&1; then
    echo "Tunel existente OK."
    echo
    return 0
  fi

  echo "Creando tunel persistente \"$TUNNEL_ID\" con acceso anonimo..."
  if "$DEVTUNNEL" create "$TUNNEL_ID" -a -d "Dev tunnel local de $DEV_USER"; then
    echo
    return 0
  fi

  echo
  echo "El Tunnel ID \"$TUNNEL_ID\" fallo o puede estar ocupado."
  echo "Generando un ID alternativo..."

  TUNNEL_ID="dev-${DEV_USER}-$RANDOM$RANDOM"
  save_config

  echo "Nuevo Tunnel ID: $TUNNEL_ID"

  if ! "$DEVTUNNEL" create "$TUNNEL_ID" -a -d "Dev tunnel local de $DEV_USER"; then
    echo
    echo "ERROR: no se pudo crear el tunel."
    exit 1
  fi

  echo
}

ensure_anonymous_access() {
  # Si ya existe, puede fallar sin ser critico.
  "$DEVTUNNEL" access create "$TUNNEL_ID" --anonymous >/dev/null 2>&1 || true
}

ensure_port() {
  local port="$1"
  local label="$2"

  echo "Verificando puerto $label $port..."

  if "$DEVTUNNEL" port show "$TUNNEL_ID" -p "$port" >/dev/null 2>&1; then
    echo "Puerto $port OK."
    echo
    return 0
  fi

  echo "Creando puerto $label $port..."

  if ! "$DEVTUNNEL" port create "$TUNNEL_ID" -p "$port" --protocol http; then
    echo
    echo "ERROR: no se pudo crear el puerto $port."
    exit 1
  fi

  echo
}

main() {
  if [[ "${1:-}" == "--reset" ]]; then
    reset_config
    exit 0
  fi

  print_header

  if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"
    echo "Config encontrada:"
    echo "  Usuario:   $DEV_USER"
    echo "  Tunnel ID: $TUNNEL_ID"
  else
    echo "Primera ejecucion."
    echo

    while true; do
      read -rp "Escribi tu nombre de usuario, por ejemplo mateo: " RAW_USER
      DEV_USER="$(normalize_user "$RAW_USER")"

      if [[ -n "$DEV_USER" ]]; then
        break
      fi

      echo "El nombre no puede estar vacio ni tener solo caracteres invalidos."
    done

    TUNNEL_ID="dev-$DEV_USER"
    save_config

    echo
    echo "Config creada:"
    echo "  Usuario:   $DEV_USER"
    echo "  Tunnel ID: $TUNNEL_ID"
  fi

  echo

  install_devtunnel_if_needed

  echo "Usando:"
  "$DEVTUNNEL" --version
  echo

  ensure_login
  ensure_tunnel
  ensure_anonymous_access
  ensure_port "$FRONT_PORT" "frontend"
  ensure_port "$BACK_PORT" "backend"

  echo "=========================================="
  echo "  Listo"
  echo "=========================================="
  echo
  echo "Antes de continuar asegurate de tener levantado:"
  echo "  Frontend: http://localhost:$FRONT_PORT"
  echo "  Backend:  http://localhost:$BACK_PORT"
  echo
  echo "Tus URLs publicas apareceran abajo como:"
  echo "  Hosting port $FRONT_PORT at https://..."
  echo "  Hosting port $BACK_PORT at https://..."
  echo
  echo "Para detenerlo: Ctrl + C"
  echo "Para cambiar de usuario: ./$(basename "$0") --reset"
  echo

  "$DEVTUNNEL" host "$TUNNEL_ID"

  echo
  echo "Dev tunnel detenido."
}

main "$@"
