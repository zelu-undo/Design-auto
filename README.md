# 🏭 ArtisanAI Studio

**Fábrica autônoma de design 100% local** - otimizada para Google Colab (GPU T4). Sem APIs, sem custos.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

---

## 🎯 O que é?

ArtisanAI Studio gera imagens automaticamente a partir de uma descrição textual. Você diz o que quer, e o sistema:

1. **Analisa** sua ideia
2. **Cria** prompts otimizados
3. **Gera** imagens com FLUX
4. **Avalia** automaticamente (4 critérios)
5. **Repete** se necessário

Tudo roda no seu Colab com GPU T4.

---

## 🏗️ Arquitetura (4 Agentes)

```
┌─────────────────────────────────────────────────────────────┐
│              ORQUESTRADOR                                    │
├─────────────────────────────────────────────────────────────┤
│  [Briefing] → [Analisador] → [Prompter] → [Designer] → [Juiz]  │
│       ↓            ↓           ↓          ↓           ↓        │
│     style      prompts    imagens    avaliação                │
│     guide               geradas     ↓                         │
│                              │                         │
│                     Aprovada? → Sim → ✅ Salva              │
│                        │                               │
│                       Não → 🔁 Refaz (max 3x)             │
└─────────────────────────────────────────────────────────────┘
```

| Agente | Modelo | Função |
|--------|--------|--------|
| **Analisador** | Qwen2.5-VL | Extrai estilo (cores, luz, mood) |
| **Prompter** | Phi-3-mini | Cria prompts otimizados |
| **Designer** | FLUX.1-schnell-FP8 | Gera imagens |
| **Juiz** | CLIP + HPSv2 | Valida qualidade |

---

## 🎨 Juiz (4 Critérios de Avaliação)

O Juiz avalia cada imagem antes de aprovar:

| # | Critério | Modelo | O que avalia | Limiar |
|---|---------|--------|-------------|-------|
| 1 | **Técnica** | BRISQUE + NIQE | Borrão, ruído | BRISQUE < 35 |
| 2 | **Estética** | HPSv2 | Beleza humana | HPS > 0.28 |
| 3 | **Fidelidade** | CLIP | Segue o prompt? | CLIP > 0.32 |
| 4 | **Rosto** | Haar Cascade | Qualidade facial | score < 0.3 |

**Imagem só é aprovada se passar em TODOS os critérios.**

---

## 🚀 Quick Start (Colab)

1. Abra: https://colab.research.google.com/github.com/zelu-undo/Design-auto/blob/main/colab.ipynb
2. Configure: projeto, descrição, quantidade
3. Execute todas as células

```python
# Célula de configuração
projeto = "meu-logo"
descricao = "Logo moderno azul para fintech"
quantas = 3
```

---

## 📦 Modelos (baixa só 1ª vez)

| Modelo | Tamanho | Agente |
|--------|--------|--------|
| FLUX.1-schnell-FP8 | ~7GB | Designer |
| Qwen2.5-VL-7B | ~7GB | Analisador |
| Phi-3-mini-4k | ~3GB | Prompter |
| CLIP + HPSv2 | ~700MB | Juiz |

**Total: ~18GB** (só 1ª vez)

---

## 📋 Modos de Operação

| Modo | Avaliação | Uso |
|------|----------|------|
| `basic` | Técnica + Estética | Testes |
| `pro` | + Fidelidade CLIP | Projetos |
| `portfolio` | + Rostos | Alta qualidade |

---

## 📁 Estrutura

```
Design-auto/
├── colab.ipynb              # Notebook Colab
├── main.py                 # CLI
├── src/
│   ├── orquestrador.py    # Orquestra tudo
│   ├── agente_analisador.py
│   ├── agente_prompter.py
│   ├── agente_designer.py
│   └── agente_juiz.py     # 4 critérios
└── projetos/
    └── {projeto}/
        ├── style_guide.json
        ├── prompts.json
        ├── aprovadas/
        └── rejeitadas/
```

---

## 💻 Uso Local

```bash
# Instalar
pip install -r requirements.txt

# Executar
python main.py -p projeto -b "Logo azul moderno" -n 3
```

---

## 🔧 Requisitos

- Python 3.9+
- GPU com 12GB+ VRAM (T4 recommended)
- 20GB+ disco

---

## 🤝 Contribuição

```bash
git checkout -b feature/nova-funcionalidade
git commit -m "feat: nova funcionalidade"
git push origin feature/nova-funcionalidade
```

---

## 📄 Licença

MIT - Veja [LICENSE](LICENSE).

---

**Sem custos. Sem APIs. 100% local.**