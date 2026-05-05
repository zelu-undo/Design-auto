#!/usr/bin/env python3
"""
Gerenciador de Estado do Projeto
Responsável por persistir e recuperar o estado do projeto entre execuções.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class GerenciadorEstado:
    """Gerencia o estado do projeto com persistência em arquivo JSON."""
    
    def __init__(self, nome_projeto: str, pasta_projetos: str = "projetos"):
        self.nome_projeto = nome_projeto
        self.pasta_projetos = Path(pasta_projetos)
        self.pasta_projeto = self.pasta_projetos / nome_projeto
        self.arquivo_estado = self.pasta_projeto / "projeto_estado.json"
        
        # Criar diretórios necessários
        self.pasta_projeto.mkdir(parents=True, exist_ok=True)
        (self.pasta_projeto / "imagens").mkdir(exist_ok=True)
        (self.pasta_projeto / "imagens_temp").mkdir(exist_ok=True)
    
    def inicializar_estado(self, briefing: str, imagens_referencia: Optional[List[str]] = None) -> Dict[str, Any]:
        """Inicializa um novo estado de projeto."""
        estado = {
            "nome_projeto": self.nome_projeto,
            "criado_em": datetime.now().isoformat(),
            "atualizado_em": datetime.now().isoformat(),
            "etapa_atual": "inicializado",
            "briefing": briefing,
            "imagens_referencia": imagens_referencia or [],
            "style_guide": None,
            "prompts": [],
            "imagens_geradas": [],
            "imagens_aprovadas": [],
            "imagens_rejeitadas": [],
            "configuracao": {
                "num_imagens_desejadas": 10,
                "resolucao": "1024x1024",
                "formato": "feed"
            },
            "metricas": {
                "clip_score": [],
                "aesthetic_score": [],
                "brisque_score": []
            }
        }
        self.salvar_estado(estado)
        return estado
    
    def carregar_estado(self) -> Optional[Dict[str, Any]]:
        """Carrega o estado existente do projeto."""
        if self.arquivo_estado.exists():
            with open(self.arquivo_estado, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def salvar_estado(self, estado: Dict[str, Any]) -> None:
        """Salva o estado no arquivo JSON."""
        estado["atualizado_em"] = datetime.now().isoformat()
        with open(self.arquivo_estado, 'w', encoding='utf-8') as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)
    
    def atualizar_etapa(self, etapa: str) -> None:
        """Atualiza a etapa atual do pipeline."""
        estado = self.carregar_estado()
        if estado:
            estado["etapa_atual"] = etapa
            self.salvar_estado(estado)
    
    def salvar_style_guide(self, style_guide: Dict[str, Any]) -> None:
        """Salva o guia de estilo gerado pelo Analisador."""
        arquivo_style_guide = self.pasta_projeto / "style_guide.json"
        with open(arquivo_style_guide, 'w', encoding='utf-8') as f:
            json.dump(style_guide, f, indent=2, ensure_ascii=False)
        
        estado = self.carregar_estado()
        if estado:
            estado["style_guide"] = str(arquivo_style_guide)
            estado["etapa_atual"] = "style_guide_pronto"
            self.salvar_estado(estado)
    
    def carregar_style_guide(self) -> Optional[Dict[str, Any]]:
        """Carrega o guia de estilo."""
        arquivo_style_guide = self.pasta_projeto / "style_guide.json"
        if arquivo_style_guide.exists():
            with open(arquivo_style_guide, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def salvar_prompts(self, prompts: List[Dict[str, Any]]) -> None:
        """Salva os prompts gerados pelo Prompter."""
        arquivo_prompts = self.pasta_projeto / "prompts.json"
        with open(arquivo_prompts, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
        
        estado = self.carregar_estado()
        if estado:
            estado["prompts"] = prompts
            estado["etapa_atual"] = "prompts_prontos"
            self.salvar_estado(estado)
    
    def carregar_prompts(self) -> List[Dict[str, Any]]:
        """Carrega os prompts salvos."""
        arquivo_prompts = self.pasta_projeto / "prompts.json"
        if arquivo_prompts.exists():
            with open(arquivo_prompts, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def registrar_imagem_gerada(self, caminho_imagem: str, prompt: str) -> None:
        """Registra uma imagem gerada."""
        estado = self.carregar_estado()
        if estado:
            estado["imagens_geradas"].append({
                "caminho": caminho_imagem,
                "prompt": prompt,
                "gerado_em": datetime.now().isoformat(),
                "status": "pendente"
            })
            self.salvar_estado(estado)
    
    def registrar_imagem_aprovada(self, caminho_imagem: str, prompt: str, metricas: Dict[str, float]) -> None:
        """Registra uma imagem aprovada pelo Juiz."""
        estado = self.carregar_estado()
        if estado:
            # Remover de imagens_geradas se existir
            for img in estado.get("imagens_geradas", []):
                if img.get("caminho") == caminho_imagem:
                    img["status"] = "aprovada"
                    break
            
            # Adicionar a imagens_aprovadas
            estado["imagens_aprovadas"].append({
                "caminho": caminho_imagem,
                "prompt": prompt,
                "metricas": metricas,
                "aprovado_em": datetime.now().isoformat()
            })
            
            # Atualizar métricas
            estado["metricas"]["clip_score"].append(metricas.get("clip", 0))
            estado["metricas"]["aesthetic_score"].append(metricas.get("aesthetic", 0))
            estado["metricas"]["brisque_score"].append(metricas.get("brisque", 0))
            
            self.salvar_estado(estado)
    
    def registrar_imagem_rejeitada(self, caminho_imagem: str, prompt: str, motivo: str) -> None:
        """Registra uma imagem rejeitada pelo Juiz."""
        estado = self.carregar_estado()
        if estado:
            # Remover de imagens_geradas se existir
            for img in estado.get("imagens_geradas", []):
                if img.get("caminho") == caminho_imagem:
                    img["status"] = "rejeitada"
                    break
            
            # Adicionar a imagens_rejeitadas
            estado["imagens_rejeitadas"].append({
                "caminho": caminho_imagem,
                "prompt": prompt,
                "motivo": motivo,
                "rejeitado_em": datetime.now().isoformat()
            })
            self.salvar_estado(estado)
    
    def marcar_prompt_aprovado(self, prompt: str) -> None:
        """Marca um prompt como aprovado para cache."""
        prompts = self.carregar_prompts()
        for p in prompts:
            if p.get("prompt") == prompt:
                p["aprovado"] = True
        arquivo_prompts = self.pasta_projeto / "prompts.json"
        with open(arquivo_prompts, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
    
    def get_proximo_prompt(self) -> Optional[Dict[str, Any]]:
        """Retorna o próximo prompt não processado."""
        prompts = self.carregar_prompts()
        for p in prompts:
            if not p.get("processado"):
                return p
        return None
    
    def marcar_prompt_processado(self, prompt: str) -> None:
        """Marca um prompt como processado."""
        prompts = self.carregar_prompts()
        for p in prompts:
            if p.get("prompt") == prompt:
                p["processado"] = True
        arquivo_prompts = self.pasta_projeto / "prompts.json"
        with open(arquivo_prompts, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
    
    def verificar_estado_existente(self) -> bool:
        """Verifica se existe um estado salvo anteriormente."""
        return self.arquivo_estado.exists()
    
    def get_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do projeto."""
        estado = self.carregar_estado()
        if not estado:
            return {}
        
        return {
            "total_imagens_geradas": len(estado.get("imagens_geradas", [])),
            "total_imagens_aprovadas": len(estado.get("imagens_aprovadas", [])),
            "total_imagens_rejeitadas": len(estado.get("imagens_rejeitadas", [])),
            "etapa_atual": estado.get("etapa_atual", "desconhecido"),
            "metricas_media": {
                "clip": sum(estado.get("metricas", {}).get("clip_score", [])) / max(1, len(estado.get("metricas", {}).get("clip_score", []))),
                "aesthetic": sum(estado.get("metricas", {}).get("aesthetic_score", [])) / max(1, len(estado.get("metricas", {}).get("aesthetic_score", []))),
                "brisque": sum(estado.get("metricas", {}).get("brisque_score", [])) / max(1, len(estado.get("metrics", {}).get("brisque_score", [])))
            }
        }