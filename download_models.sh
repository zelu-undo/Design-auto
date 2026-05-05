#!/bin/bash
#
# Script para baixar FLUX.1 Schnell
# Execute: bash download_modelo.sh
#
# Tamanho: ~4GB
#

PASTA="modelo_cache"

if [ -d "$PASTA" ]; then
    echo "✅ Modelo já existe: $PASTA"
    exit 0
fi

echo "📦 Baixando FLUX.1-schnell (~4GB)..."
mkdir -p "$PASTA"

huggingface-cli download black-forest-labs/FLUX.1-schnell \
    --local-dir "$PASTA" \
    --local-use-symlinks False

echo "✅ Salvo em: $PASTA"
echo ""
echo "Para usar:"
echo "  modelo_local = './modelo_cache'"