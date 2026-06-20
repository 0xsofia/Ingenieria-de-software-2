#!/bin/bash

set -e

echo "==============================================="


echo "Este script es para correr Tailscale Funnel y exponer el frontend y backend a traves de Tailscale."

echo "==============================================="
echo ""

if [ "$EUID" -ne 0 ]; then
  echo "Este script necesita permisos de administrador."
  echo "Ejecutalo asi: sudo ./correrTailscale.sh"
  exit 1
fi

if ! command -v tailscale >/dev/null 2>&1; then
  echo "Tailscale no esta instalado o no esta en el PATH."
  echo "Instalalo desde https://tailscale.com/download y volve a ejecutar este script."
  exit 1
fi

if ! tailscale status >/dev/null 2>&1; then
  echo "Tailscale no esta configurado, no esta logueado o el servicio no esta corriendo."
  echo "Verifica con: sudo systemctl start tailscaled"
  echo "Luego inicia sesion con: sudo tailscale up"
  exit 1
fi

echo "Levantando Tailscale Funnel para frontend y backend..."
echo ""
echo "==============================================="
echo "Exponiendo frontend (puerto 5173 interno, 443 externo)"
echo "==============================================="
echo ""
tailscale funnel --bg localhost:5173

echo ""
echo "==============================================="
echo "Exponiendo backend (puerto 5000 interno, 8443 externo)"
echo "==============================================="

tailscale funnel --bg --https=8443 localhost:5000

echo "Listo:"
tailscale funnel status
