#!/usr/bin/env python3
"""
Agente Juiz (Controle de Qualidade)
Avalia imagens usando CLIP, Aesthetic e BRISQUE.
Suporta 3 modos: Básico, Profissional (manual), Portfólio (rigoroso).
"""

import gc
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Imports para produção
try:
    from transformers import CLIPProcessor, CLIPModel
    from PIL import Image
    import cv2
    import numpy as np
    TORCH_DISPONIVEL = True
except ImportError:
    TORCH_DISPONIVEL = False
    CLIPProcessor = None
    CLIPModel = None
    Image = None
    cv2 = None
    np = None


class ModoAvaliacao(Enum):
    """Modos de avaliação do Juiz."""
    BASIC = "basic"       # CLIP > 0.25, Aesthetic >= 5.5, BRISQUE < 30
    PROFISSIONAL = "pro"  # Apenas BRISQUE < 40 (avaliação manual via Gradio)
    PORTFOLIO = "portfolio"  # CLIP > 0.32, Aesthetic >= 6.0, BRISQUE < 25


class AgenteJuiz:
    """Agente que avalia imagens."""
    
    # Modelos para validação estética
    MODELO_CLIP = "openai/clip-vit-large-patch14"
    MODELO_HPSV2 = "yilundu/HPSv2"
    
    # Limiares por modo
    LIMIARES = {
        ModoAvaliacao.BASIC: {
            "clip": 0.25,
            "aesthetic": 5.5,
            "brisque": 30.0
        },
        ModoAvaliacao.PROFISSIONAL: {
            "brisque": 40.0
        },
        ModoAvaliacao.PORTFOLIO: {
            "clip": 0.32,
            "aesthetic": 6.0,
            "brisque": 25.0
        }
    }
    
    def __init__(self, modo: str = "basic"):
        self.modo = ModoAvaliacao(modo) if modo in [m.value for m in ModoAvaliacao] else ModoAvaliacao.BASIC
        self.modelo_clip = None
        self.processor_clip = None
        self.modelo_aesthetic = None
        self.resultados = []
    
    def _carregar_clip(self) -> Tuple[Any, Any]:
        """Carrega o modelo CLIP (em CPU para todos os modos)."""
        # Código real (descomentar em produção)
        # modelo_id = "openai/clip-vit-large-patch14"
        # self.modelo_clip = CLIPModel.from_pretrained(modelo_id)
        # self.processor_clip = CLIPProcessor.from_pretrained(modelo_id)
        
        self.modelo_clip = "mock_clip"
        self.processor_clip = "mock_processor"
        return self.modelo_clip, self.processor_clip
    
    def _carregar_aesthetic(self) -> Any:
        """Carrega o modelo Aesthetic Predictor (em CPU para todos os modos)."""
        # Código real
        # from huggingface_hub import hf_hub_download
        # modelo_path = hf_hub_download(repo_id="youngfor5/aesthetic_predictor", filename="model.pth")
        # self.modelo_aesthetic = carregar_modelo(modelo_path)
        
        self.modelo_aesthetic = "mock_aesthetic"
        return self.modelo_aesthetic
    
    def _verificar_rosto(self, caminho_imagem: str) -> bool:
        """Detecta rosto na imagem (Modo Portfólio, para prompts de retrato)."""
        # Código real
        # import cv2
        # img = cv2.imread(caminho_imagem)
        # cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # rostos = detector.detectMultiScale(cinza, 1.1, 4)
        # return len(rostos) > 0
        
        return True  # Mock
    
    def avaliar_clip(self, caminho_imagem: str, prompt: str) -> float:
        """Avalia similaridade semântica entre imagem e prompt usando CLIP."""
        if self.modelo_clip is None:
            self._carregar_clip()
        
        # Código real (descomentar em produção)
        # imagem = Image.open(caminho_imagem).convert("RGB")
        # inputs = self.processor_clip(text=prompt, images=imagem, return_tensors="pt")
        # with torch.no_grad():
        #     outputs = self.modelo_clip(**inputs)
        #     probs = outputs.logits_per_image.softmax(dim=1)
        # return probs[0][1].item()
        
        # Mock: retornar score aleatório
        import hashlib
        hash_val = int(hashlib.md5(f"{caminho_imagem}{prompt}".encode()).hexdigest(), 16)
        return (hash_val % 100) / 100
    
    def avaliar_aesthetic(self, caminho_imagem: str) -> float:
        """Avalia pontuação estética da imagem."""
        if self.modelo_aesthetic is None:
            self._carregar_aesthetic()
        
        # Código real
        # import cv2
        # img = cv2.imread(caminho_imagem)
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # img = cv2.resize(img, (224, 224))
        # tensor = torch.tensor(img).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        # with torch.no_grad():
        #     score = self.modelo_aesthetic(tensor)
        # return score.item()
        
        # Mock
        import hashlib
        hash_val = int(hashlib.md5(caminho_imagem.encode()).hexdigest(), 16)
        return 3.0 + (hash_val % 70) / 10
    
    def avaliar_brisque(self, caminho_imagem: str) -> float:
        """Avalia qualidade técnica usando BRISQUE."""
        # Código real
        # import cv2
        # img = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)
        # if img is None:
        #     return 100.0
        # img = cv2.resize(img, (256, 256))
        # # Calcular features do BRISQUE (simplificado)
        # quality = calcular_brisque_features(img)
        # return quality
        
        # Mock
        import hashlib
        hash_val = int(hashlib.md5(caminho_imagem.encode()).hexdigest(), 16)
        return 10.0 + (hash_val % 40)
    
    def avaliar_imagem(
        self, 
        caminho_imagem: str, 
        prompt: str = "",
        calcular_brisque: bool = True
    ) -> Dict[str, float]:
        """
        Avalia uma imagem com todas as métricas.
        
        Args:
            caminho_imagem: Caminho para a imagem
            prompt: Prompt original
            calcular_brisque: Se calcular BRISQUE
            
        Returns:
            Dicionário com scores
        """
        limiares = self.LIMIARES.get(self.modo, self.LIMIARES[ModoAvaliacao.BASIC])
        
        # Avaliar CLIP (se aplicável)
        clip_score = 0.0
        if "clip" in limiares:
            clip_score = self.avaliar_clip(caminho_imagem, prompt)
        
        # Avaliar Aesthetic (se aplicável)
        aesthetic_score = 0.0
        if "aesthetic" in limiares:
            aesthetic_score = self.avaliar_aesthetic(caminho_imagem)
        
        # Avaliar BRISQUE (se aplicável)
        brisque_score = 100.0
        if calcular_brisque and "brisque" in limiares:
            brisque_score = self.avaliar_brisque(caminho_imagem)
        
        # Verificar aprovação
        aprovado = True
        if "clip" in limiares:
            aprovado = aprovado and clip_score >= limiares["clip"]
        if "aesthetic" in limiares:
            aprovado = aprovado and aesthetic_score >= limiares["aesthetic"]
        if "brisque" in limiares:
            aprovado = aprovado and brisque_score < limiares["brisque"]
        
        # Modo Portfólio: verificar rosto para prompts de retrato
        if self.modo == ModoAvaliacao.PORTFOLIO:
            if "retrato" in prompt.lower() or "portrait" in prompt.lower() or "face" in prompt.lower():
                tem_rosto = self._verificar_rosto(caminho_imagem)
                aprovado = aprovado and tem_rosto
        
        resultado = {
            "clip": clip_score,
            "aesthetic": aesthetic_score,
            "brisque": brisque_score,
            "aprovado": aprovado,
            "detalhes": limiares
        }
        
        self.resultados.append({
            "imagem": caminho_imagem,
            "prompt": prompt,
            **resultado
        })
        
        return resultado
    
    def avaliar_batch(
        self, 
        imagens: List[Dict[str, str]],
        continuar_em_erro: bool = True
    ) -> List[Dict[str, Any]]:
        """Avalia um batch de imagens."""
        resultados = []
        
        for img in imagens:
            caminho = img.get("caminho", "")
            prompt = img.get("prompt", "")
            
            if not caminho:
                resultados.append({"erro": "Caminho vazio"})
                if not continuar_em_erro:
                    continue
                continue
            
            try:
                avaliacao = self.avaliar_imagem(caminho, prompt)
                resultados.append({
                    "caminho": caminho,
                    "prompt": prompt,
                    **avaliacao
                })
            except Exception as e:
                resultados.append({
                    "caminho": caminho,
                    "prompt": prompt,
                    "erro": str(e)
                })
        
        return resultados
    
    def get_estatisticas(self) -> Dict[str, Any]:
        """Calcula estatísticas das avaliações."""
        if not self.resultados:
            return {}
        
        clip_scores = []
        aesthetic_scores = []
        brisque_scores = []
        aprovados = 0
        reprovados = 0
        
        for r in self.resultados:
            if "clip" in r and r.get("clip", 0) > 0:
                clip_scores.append(r["clip"])
            if "aesthetic" in r and r.get("aesthetic", 0) > 0:
                aesthetic_scores.append(r["aesthetic"])
            if "brisque" in r and r.get("brisque", 100) < 100:
                brisque_scores.append(r["brisque"])
            if r.get("aprovado"):
                aprovados += 1
            else:
                reprovados += 1
        
        total = len(self.resultados)
        
        def avg(lst):
            return sum(lst) / len(lst) if lst else 0
        
        return {
            "total": total,
            "aprovadas": aprovados,
            "reprovadas": reprovados,
            "taxa_aprovacao": aprovados / total if total > 0 else 0,
            "media_clip": avg(clip_scores),
            "media_aesthetic": avg(aesthetic_scores),
            "media_brisque": avg(brisque_scores)
        }
    
    def verificar_aprovacao(self, avaliacao: Dict[str, float]) -> Tuple[bool, str]:
        """Verifica se uma avaliação resultou em aprovação."""
        if not avaliacao.get("aprovado"):
            motivos = []
            limiares = self.LIMIARES.get(self.modo, {})
            
            if "clip" in limiares and avaliacao.get("clip", 0) < limiares["clip"]:
                motivos.append(f"CLIP {avaliacao.get('clip', 0):.2f} < {limiares['clip']}")
            
            if "aesthetic" in limiares and avaliacao.get("aesthetic", 0) < limiares["aesthetic"]:
                motivos.append(f"Aesthetic {avaliacao.get('aesthetic', 0):.1f} < {limiares['aesthetic']}")
            
            if "brisque" in limiares and avaliacao.get("brisque", 100) >= limiares["brisque"]:
                motivos.append(f"BRISQUE {avaliacao.get('brisque', 0):.1f} >= {limiares['brisque']}")
            
            return False, "; ".join(motivos)
        
        return True, "Aprovado"
    
    def recomendar_acao(
        self, 
        avaliacao: Dict[str, float],
        tentativas: int,
        max_tentativas: int = 3
    ) -> str:
        """Recommenda ação baseado na avaliação."""
        if avaliacao.get("aprovado"):
            return "aprovar"
        
        if tentativas < max_tentativas:
            return "regerar"
        
        return "descartar"
    
    def limpar_resultados(self) -> None:
        """Limpa resultados armazenados."""
        self.resultados = []
    
    def get_modo(self) -> str:
        """Retorna o modo atual."""
        return self.modo.value
    
    def set_modo(self, modo: str) -> None:
        """Define o modo de avaliação."""
        self.modo = ModoAvaliacao(modo)