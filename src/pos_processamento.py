#!/usr/bin/env python3
"""
Pós-processamento para Modo Portfólio
Aplica ajustes leves para melhorar qualidade das imagens geradas.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Try import PIL
try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_DISPONIVEL = True
except ImportError:
    PIL_DISPONIVEL = False


class PosProcessamento:
    """Aplica pós-processamento leve às imagens geradas."""
    
    # Configurações padrão
    CONTRASTE_AUMENTO = 0.05  # +5%
    NITIDEZ_RAIO = 0.5
    NITIDEZ_INTENSIDADE = 0.3
    SATURACAO_AUMENTO = 0.02  # +2%
    
    def __init__(self):
        self.processamentos_aplicados = []
    
    def verificar_pIL(self) -> bool:
        """Verifica se PIL está disponível."""
        if not PIL_DISPONIVEL:
            print("⚠️ PIL não disponível. Execute: pip install pillow")
        return PIL_DISPONIVEL
    
    def aplicar_contraste(
        self, 
        imagem: Image.Image,
        fator: float = CONTRATE_AUMENTO
    ) -> Image.Image:
        """Aumenta contraste em X%."""
        enhancer = ImageEnhance.Contrast(imagem)
        return enhancer.enhance(1.0 + fator)
    
    def aplicar_nitidez(
        self, 
        imagem: Image.Image,
        raio: float = NITIDEZ_RAIO,
        intensidade: float = NITIDEZ_INTENSIDADE
    ) -> Image.Image:
        """Aplica nitidez."""
        return imagem.filter(
            ImageFilter.UnsharpMask(
                radius=raio, 
                percent=int(intensidade * 100)
            )
        )
    
    def aplicar_saturacao(
        self, 
        imagem: Image.Image,
        fator: float = SATURACAO_AUMENTO
    ) -> Image.Image:
        """Aumenta saturação em X%."""
        enhancer = ImageEnhance.Color(imagem)
        return enhancer.enhance(1.0 + fator)
    
    def aplicar_todos(
        self, 
        caminho: str,
        contraste: bool = True,
        nitidez: bool = True,
        saturacao: bool = True
    ) -> Tuple[Path, Dict[str, bool]]:
        """
        Aplica todos os pós-processamentos configurados.
        
        Args:
            caminho: Caminho da imagem
            contraste: Aplicar contraste
            nitidez: Aplicar nitidez
            saturacao: Aplicar saturação
            
        Returns:
            Tupla (novo_caminho, processamentos)
        """
        if not self.verificar_pIL():
            return Path(caminho), {}
        
        # Carregar imagem
        img = Image.open(caminho)
        processamentos = {}
        
        # Aplicarコントラスト
        if contraste:
            img = self.aplicar_contraste(img)
            processamentos["contraste"] = True
        
        # Aplicar nitidez
        if nitidez:
            img = self.aplicar_nitidez(img)
            processamentos["nitidez"] = True
        
        # Aplicar saturação
        if saturacao:
            img = self.aplicar_saturacao(img)
            processamentos["saturacao"] = True
        
        # Salvar imagem processada
        caminho_obj = Path(caminho)
        nome = caminho_obj.stem + "_pp" + caminho_obj.suffix
        novo_caminho = caminho_obj.parent / nome
        
        img.save(novo_caminho)
        
        self.processamentos_aplicados.append({
            "original": str(caminho),
            "processado": str(novo_caminho),
            "processamentos": processamentos
        })
        
        return novo_caminho, processamentos
    
    def processar_batch(
        self,
        caminhos,
        **kwargs
    ) -> Any:
        """Processa múltiplas imagens."""
        resultados = []
        
        for caminho in caminhos:
            try:
                novo_caminho, processamentos = self.aplicar_todos(caminho, **kwargs)
                resultados.append({
                    "original": caminho,
                    "processado": str(novo_caminho),
                    "sucesso": True,
                    "processamentos": processamentos
                })
            except Exception as e:
                resultados.append({
                    "original": caminho,
                    "sucesso": False,
                    "erro": str(e)
                })
        
        return resultados
    
    def get_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do pós-processamento."""
        return {
            "total_processado": len(self.processamentos_aplicados),
            "detalhes": self.processamentos_aplicados
        }


class CachePromptsVencedores:
    """Cache de prompts que geraram imagens de alta qualidade."""
    
    def __init__(self, arquivo: str = "src/prompts_vencedores.csv"):
        self.arquivo = Path(arquivo)
        self.prompts = []
        self._carregar()
    
    def _carregar(self) -> None:
        """Carrega prompts do arquivo."""
        if not self.arquivo.exists():
            return
        
        try:
            import csv
            with open(self.arquivo, 'r') as f:
                reader = csv.DictReader(f)
                self.prompts = list(reader)
        except Exception as e:
            print(f"Erro ao carregar prompts: {e}")
    
    def _salvar(self) -> None:
        """Salva prompts no arquivo."""
        try:
            import csv
            with open(self.arquivo, 'w', newline='') as f:
                if self.prompts:
                    writer = csv.DictWriter(f, fieldnames=self.prompts[0].keys())
                    writer.writeheader()
                    writer.writerows(self.prompts)
        except Exception as e:
            print(f"Erro ao salvar prompts: {e}")
    
    def adicionar(
        self,
        prompt: str,
        aesthetic: float,
        clip: float,
        brisque: float
    ) -> None:
        """Adiciona um prompt vencedor."""
        import datetime
        
        self.prompts.append({
            "prompt": prompt,
            "aesthetic": str(aesthetic),
            "clip": str(clip),
            "brisque": str(brisque),
            "data": datetime.datetime.now().isoformat()
        })
        
        self._salvar()
    
    def buscar_similar(self, novo_prompt: str, threshold: float = 0.6) -> Optional[str]:
        """
        Busca prompt similar no cache.
        
        Args:
            novo_prompt: Prompt a buscar similaridade
            threshold: Limiar de similaridade
            
        Returns:
            Prompt similar ou None
        """
        if not self.prompts:
            return None
        
        novo_lower = novo_prompt.lower()
        
        for p in self.prompts:
            prompt_existente = p.get("prompt", "").lower()
            
            # Similaridade simples: palavras em comum
            palavras_novo = set(novo_lower.split())
            palavras_existente = set(prompt_existente.split())
            
            if not palavras_existente:
                continue
            
            similaridade = len(palavras_novo & palavras_existente) / len(palavras_novo | palavras_existente)
            
            if similaridade >= threshold:
                return p.get("prompt")
        
        return None
    
    def get_melhor_prompt(self) -> Optional[str]:
        """Retorna o prompt com maior aesthetic."""
        if not self.prompts:
            return None
        
        melhor = max(
            self.prompts,
            key=lambda p: float(p.get("aesthetic", 0))
        )
        
        return melhor.get("prompt")
    
    def get_top_prompts(self, limit: int = 5) -> list:
        """Retorna os top N prompts por aesthetic."""
        if not self.prompts:
            return []
        
        ordenados = sorted(
            self.prompts,
            key=lambda p: float(p.get("aesthetic", 0)),
            reverse=True
        )
        
        return ordenados[:limit]