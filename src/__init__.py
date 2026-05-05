"""
ArtisanAI Studio - Fábrica de Design Autônoma

Pacote principal contendo os módulos do sistema:
- gerenciador_estado: Persistência de estado do projeto
- agente_analisador: Análise de estilo
- agente_prompter: Geração de prompts
- agente_designer: Geração de imagens
- agente_juiz: Avaliação de qualidade
- orquestrador: Coordenação do pipeline
"""

from .gerenciador_estado import GerenciadorEstado
from .agente_analisador import AgenteAnalisador
from .agente_prompter import AgentePrompter
from .agente_designer import AgenteDesigner
from .agente_juiz import AgenteJuiz
from .orquestrador import Orquestrador

__all__ = [
    "GerenciadorEstado",
    "AgenteAnalisador",
    "AgentePrompter",
    "AgenteDesigner",
    "AgenteJuiz",
    "Orquestrador"
]

__version__ = "1.0.0"