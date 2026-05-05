#!/bin/bash
#
# Script para baixar TODOS os modelos de IA
# Execute: bash download_models.sh
#
# Tamanho total: ~10GB
#

set -e

PASTA_MODELOS="modelo_cache"
mkdir -p "$PASTA_MODELOS"

echo "📦 Baixando todos os modelos..."
echo "Tamanho total: ~10GB"
echo ""

# Modelos disponíveis
MODELOS=(
    "stabilityai/sdxl-turbo:sdxl-turbo"
    "stabilityai/stable-diffusion-xl-base-1.0:sdxl-base"
    "black-forest-labs/FLUX.1-schnell:flux-schnell"
)

for item in "${MODELOS[@]}"; do
    repo_id="${item%%:*}"
    nome="${item##*:}"
    
    pasta="$PASTA_MODELOS/$nome"
    
    if [ -d "$pasta" ]; then
        echo "✅ $nome já existe"
    else
        echo "📦 Baixando $nome..."
        huggingface-cli download "$repo_id" \
            --local-dir "$pasta" \
            --local-use-symlinks False
        echo "✅ $nome salvo!"
    fi
done

echo ""
echo "✅ Todos os modelos salvos em: $PASTA_MODELOS/"
echo ""
echo "Para usar no projeto:"
echo "  basic:  modelo_local = './modelo_cache/sdxl-turbo'"
echo "  pro:    modelo_local = './modelo_cache/flux-schnell'"