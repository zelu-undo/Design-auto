#!/bin/bash
#
# Script para baixar modelos de IA
# Execute: bash download_models.sh
#

set -e

PASTA_MODELOS="modelos"
mkdir -p "$PASTA_MODELOS"

echo "📦 Baixando modelos..."

# SDXL-Turbo (~2GB)
echo "1. Baixando SDXL-Turbo..."
huggingface-cli download stabilityai/sdxl-turbo \
    --local-dir "$PASTA_MODELOS/sdxl-turbo" \
    --local-use-symlinks False

echo "✅ Modelos baixados em: $PASTA_MODELOS/"
echo ""
echo "Para usar no projeto:"
echo "  modelo_local = './modelos/sdxl-turbo'"