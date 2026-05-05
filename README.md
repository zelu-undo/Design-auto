# 🏭 ArtisanAI Studio

**100% local, free autonomous design factory** - optimized for Google Colab (T4 GPU).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

ArtisanAI Studio é uma fábrica autônoma de design que usa IA para gerar imagens a partir de briefings textuais. Suporta múltiplos modos de operação e avaliação automática ou manual.

## ✨ Recursos

- **3 Modos de Operação**: Basic, Professional, Portfolio
- **Geração Local**: Sem custos de API - tudo roda na sua GPU
- **Avaliação Automática**: CLIP, Aesthetic Score, BRISQUE
- **Revisão Manual**: Interface Gradio opcional
- **Metadados Falsos**: Anonimiza imagens geradas
- **Análise de Sites**: Extrai estilo de websites e Instagram

## 🚀 Quick Start

```bash
# Clone o projeto
git clone https://github.com/zelu-undo/Design-auto.git
cd Design-auto

# Instale as dependências (ambiente com GPU recomendado)
pip install -r requirements.txt

# Execute via CLI
python main.py -p meu_projeto -b "Fashion moderna" -n 5

# OU execute via GUI
python main.py --gui
```

## 📋 Modos de Operação

| Modo | Modelo | Resolução | Automação | Uso |
|------|--------|-----------|----------|---------|
| `basic` | SDXL-Turbo | 768×768 | ✅ Automática | Testes, protótipos |
| `pro` | Flux.1 Schnell | 1024×1024 | ❌ Revisão manual | Projetos profissionais |
| `portfolio` | Flux.1 Schnell | 1024×1024 | ✅ Rigorosa | Portfólio, alta qualidade |

### Exemplos:

```bash
# Modo básico (padrão)
python main.py -p projeto1 -b "Fashion elegante" -n 10

# Modo profissional (com revisão manual)
python main.py -p projeto2 -b "Logo startup" --modo pro

# Modo portfólio (avaliação rigorosa)
python main.py -p projeto3 -b "Produto premium" --modo portfolio
```

## 🔧 Opções Avançadas

### Metadados Falsos

Adiciona metadados de câmera profissional para anonimizar imagens geradas por IA:

```bash
python main.py -p projeto -b "Fashion" --metadados --camera canon_eos
```

Câmeras disponíveis: `canon_eos` (padrão), `nikon_d850`, `sony_a7r`

### Análise de Website

Extrai paleta de cores e estilo de qualquer site:

```bash
python main.py --analisar-site https://exemplo.com
```

### Análise de Instagram

Calcula consistência visual de um perfil:

```bash
python main.py --analisar-instagram @empresa
```

## 📁 Estrutura do Projeto

```
Design-auto/
├── main.py                    # Ponto de entrada
├── requirements.txt          # Dependências
├── TODO.md               # Especificações técnicas
├── .gitignore
├── projetos/            # Projetos gerados
│   └── [projeto]/
│       ├── style_guide.json
│       ├── prompts.json
│       ├── aprovadas/
│       └── rejeitadas/
└── src/
    ├── __init__.py
    ├── orquestrador.py     # Orquestrador principal
    ├── agente_analisador.py  # Análise de estilo
    ├── agente_prompter.py  # Geração de prompts
    ├── agente_designer.py  # Geração de imagens
    ├── agente_juiz.py    # Avaliação de qualidade
    ├── gerenciador_estado.py  # Persistência
    ├── interface_gradio.py  # UI Gradio
    ├── pos_processamento.py  # Pós-processamento
    ├── metadados.py     # Metadados EXIF
    └── analisador_site.py  # Análise de sites
```

## 🎯 Como Funciona

### Pipeline Completo

1. **Analisador** - Extrai paleta de cores e estilo do briefing
2. **Prompter** - Gera prompts otimizados para o modelo
3. **Designer** - Gera imagens usando SDXL-Turbo ou Flux.1
4. **Juiz** - Avalia qualidade (CLIP, Aesthetic, BRISQUE)
5. **Loop** - Repete até atingir meta de imagens aprovadas

### Avaliação

Cada imagem é avaliada por 3 métricas:

| Métrica | Descrição | thresholds |
|---------|----------|-----------|
| CLIP | Similaridade texto-imagem | > 0.25 (basic), > 0.32 (portfolio) |
| Aesthetic | Beleza perceptual | ≥ 5.5 (basic), ≥ 6.0 (portfolio) |
| BRISQUE | Qualidade técnica | < 30 (basic), < 25 (portfolio) |

## 🖥️ Interface Gradio

No modo `pro`, abre interface para revisão manual:

```bash
python main.py -p projeto -b "Logo" --modo pro
# Abre automaticamente em: http://localhost:7860
```

## ☁️ Google Colab

### Um Clique

Abra o notebook direto no Colab:

https://colab.research.google.com/github.com/zelu-undo/Design-auto/blob/main/colab.ipynb

### Configurações Recomendadas

| setting | Value |
|---------|-------|
| Runtime | T4 GPU |
| Ram | High (12GB) |
| Tempo | Infinite |

## 💻 Ambiente Google Colab

```python
# Célula 1: Instalar dependências
!pip install -r requirements.txt
!apt-get update && apt-get install -y git

# Célula 2: Clonar e executar
!git clone https://github.com/zelu-undo/Design-auto.git
%cd Design-auto
!python main.py -p projeto -b "Fashion" -n 5
```

## ⚙️ Requisitos

- Python 3.9+
- GPU com 8GB+ VRAM (T4 recommended)
- 15GB+ disco

### Dependências Principais

- `torch` + `diffusers`
- `transformers` + `bitsandbytes`
- `gradio` (interface)
- `piexif` (metadados)
- `beautifulsoup4` + `requests` (análise de sites)

## 🤝 Contribuição

```bash
# Fork
# Clone seu fork
# Create branch
git checkout -b feature/nova-funcionalidade
# Commit
git commit -m "feat: nova funcionalidade"
# Push
git push origin feature/nova-funcionalidade
# PR
```

## 📄 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes.

---

**Nota**: Este projeto funciona em modo mock sem GPU. Para geração real, instale as dependências e execute em ambiente com GPU T4 ou superior.