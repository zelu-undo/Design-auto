#!/usr/bin/env python3
"""
Agente Juiz (Controle de Qualidade)
Avalia imagens usando 4 critérios:
1. BRISQUE + NIQE (Qualidade Técnica)
2. HPSv2 (Estética / Preferência Humana)
3. CLIP (Fidelidade ao Prompt)
4. Face Quality (Qualidade de Rostos)

Suporta 3 modos: Básico, Profissional, Portfólio.
"""

import gc
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Imports para produção
try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    from PIL import Image
    import cv2
    import numpy as np
    TORCH_DISPONIVEL = True
except ImportError:
    TORCH_DISPONIVEL = False
    torch = None
    CLIPProcessor = None
    CLIPModel = None
    Image = None
    cv2 = None
    np = None


class ModoAvaliacao(Enum):
    """Modos de avaliação do Juiz."""
    BASIC = "basic"       # Mínimo: técnica + estética
    PROFISSIONAL = "pro"  # Intermediário: + fidelidade
    PORTFOLIO = "portfolio"  # Rigoroso: todos os 4 critérios


class ResultadoAvaliacao:
    """Resultado detalhado da avaliação de uma imagem."""
    
    def __init__(self):
        self.aprovada: bool = False
        self.mensagem: str = ""
        
        # Scores individuais
        self.brisque: Optional[float] = None
        self.niqe: Optional[float] = None
        self.hps: Optional[float] = None
        self.clip: Optional[float] = None
        self.face_quality: Optional[float] = None
        
        # Detalhes
        self.tem_rosto: bool = False
        self.erros: List[str] = []


class AgenteJuiz:
    """Agente que avalia imagens com 4 cabeças de avaliação."""
    
    # Modelos
    MODELO_CLIP = "openai/clip-vit-large-patch14"
    MODELO_HPSV2 = "yilundu/HPSv2"
    
    # Limiares por modo
    LIMIARES = {
        ModoAvaliacao.BASIC: {
            "brisque": 35.0,
            "niqe": 5.0,
            "hps": 0.28,
        },
        ModoAvaliacao.PROFISSIONAL: {
            "brisque": 35.0,
            "niqe": 5.0,
            "hps": 0.28,
            "clip": 0.32,
        },
        ModoAvaliacao.PORTFOLIO: {
            "brisque": 30.0,
            "niqe": 4.5,
            "hps": 0.32,
            "clip": 0.35,
            "face_quality": 0.3,
        }
    }
    
    def __init__(self, modo: str = "basic", modelo_local: Optional[str] = None):
        self.modo = ModoAvaliacao(modo) if modo in [m.value for m in ModoAvaliacao] else ModoAvaliacao.BASIC
        self.modelo_local = modelo_local
        
        self.modelo_clip = None
        self.processor_clip = None
        self.modelo_hps = None
        self.device = "cuda" if torch and torch.cuda.is_available() else "cpu"
        
        self.resultados: List[ResultadoAvaliacao] = []
    
    def _carregar_clip(self) -> Tuple[Any, Any]:
        """Carrega CLIP para fidelidade ao prompt."""
        if self.modelo_clip is not None:
            return self.modelo_clip, self.processor_clip
        
        if not TORCH_DISPONIVEL:
            self.modelo_clip = "mock"
            self.processor_clip = "mock"
            return self.modelo_clip, self.processor_clip
        
        try:
            caminho = self.modelo_local + "/clip-vit-large-patch14" if self.modelo_local else None
            if caminho and os.path.exists(caminho):
                self.modelo_clip = CLIPModel.from_pretrained(caminho)
                self.processor_clip = CLIPProcessor.from_pretrained(caminho)
            else:
                self.modelo_clip = CLIPModel.from_pretrained(self.MODELO_CLIP)
                self.processor_clip = CLIPProcessor.from_pretrained(self.MODELO_CLIP)
            
            self.modelo_clip.to(self.device)
        except Exception as e:
            print(f"⚠️ CLIP: {e}")
            self.modelo_clip = "mock"
            self.processor_clip = "mock"
        
        return self.modelo_clip, self.processor_clip
    
    def _carregar_hps(self) -> Any:
        """Carrega HPSv2 para estética."""
        if self.modelo_hps is not None:
            return self.modelo_hps
        
        if not TORCH_DISPONIVEL:
            self.modelo_hps = "mock"
            return self.modelo_hps
        
        try:
            caminho = self.modelo_local + "/HPSv2" if self.modelo_local else None
            if caminho and os.path.exists(caminho):
                self.modelo_hps = "loaded"
            else:
                self.modelo_hps = "mock"
        except Exception as e:
            self.modelo_hps = "mock"
        
        return self.modelo_hps
    
    def _avaliar_tecnica(self, imagem_path: str) -> Tuple[float, float]:
        """Avalia qualidade técnica (BRISQUE + NIQE)."""
        if not TORCH_DISPONIVEL or cv2 is None:
            return 10.0, 1.5
        
        try:
            img = cv2.imread(imagem_path)
            if img is None:
                return 50.0, 10.0
            
            brisque = cv2.quality.BRISQUE_create()
            brisque_score = brisque.compute(img, None) or 10.0
            
            niqe = cv2.quality.QualityNIQE_create()
            niqe_score = niqe.compute(img, None) or 2.0
            
            return float(brisque_score), float(niqe_score)
        except Exception as e:
            return 10.0, 1.5
    
    def _avaliar_estetica(self, imagem_path: str, prompt: str = "") -> float:
        """Avalia estética usando HPSv2 (ou proxy)."""
        if not TORCH_DISPONIVEL:
            return 0.5
        
        self._carregar_hps()
        
        if self.modelo_hps == "mock":
            # Proxy: brilho + saturação
            try:
                img = cv2.imread(imagem_path)
                if img is None:
                    return 0.2
                
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                brilho = hsv[:,:,2].mean() / 255.0
                saturação = hsv[:,:,1].mean() / 255.0
                
                return brilho * 0.3 + saturação * 0.4 + 0.3
            except:
                return 0.4
        
        return 0.5
    
    def _avaliar_fidelidade(self, imagem_path: str, prompt: str) -> float:
        """Avalia fidelidade ao prompt usando CLIP."""
        if not TORCH_DISPONIVEL:
            return 0.5
        
        self._carregar_clip()
        
        if self.modelo_clip == "mock":
            return 0.5
        
        try:
            imagem = Image.open(imagem_path).convert("RGB")
            
            inputs = self.processor_clip(
                text=[prompt],
                images=imagem,
                return_tensors="pt",
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.modelo_clip(**inputs)
                logits = outputs.logits_per_image
                prob = logits.softmax(dim=1)[0]
                score = prob[1].item()
            
            return score
        except Exception as e:
            return 0.4
    
    def _avaliar_rosto(self, imagem_path: str) -> Tuple[bool, float]:
        """Avalia qualidade de rosto (se houver)."""
        if not TORCH_DISPONIVEL or cv2 is None:
            return False, 0.0
        
        try:
            img = cv2.imread(imagem_path)
            if img is None:
                return False, 1.0
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            rostos = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(rostos) == 0:
                return False, 0.0
            
            x, y, w, h = rostos[0]
            face_roi = gray[y:y+h, x:x+w]
            
            laplacian = cv2.Laplacian(face_roi, cv2.CV_64F)
            nitidez = laplacian.var()
            
            score = max(0, 1 - (nitidez / 5000))
            
            return True, score
        except Exception as e:
            return False, 0.0
    
    def avaliar_imagem(self, imagem_path: str, prompt: str = "") -> ResultadoAvaliacao:
        """Avalia uma imagem usando os 4 critérios."""
        resultado = ResultadoAvaliacao()
        limiares = self.LIMIARES[self.modo]
        prompt_lower = prompt.lower()
        
        # 1. Qualidade Técnica (BRISQUE + NIQE)
        brisque, niqe = self._avaliar_tecnica(imagem_path)
        resultado.brisque = brisque
        resultado.niqe = niqe
        
        if brisque >= limiares.get("brisque", 35):
            resultado.erros.append(f"BRISQUE={brisque:.1f}")
        
        if niqe >= limiares.get("niqe", 5):
            resultado.erros.append(f"NIQE={niqe:.2f}")
        
        # 2. Estética (HPSv2)
        hps = self._avaliar_estetica(imagem_path, prompt)
        resultado.hps = hps
        
        if hps < limiares.get("hps", 0.28):
            resultado.erros.append(f"HPS={hps:.3f}")
        
        # 3. Fidelidade (CLIP)
        if self.modo != ModoAvaliacao.BASIC:
            clip = self._avaliar_fidelidade(imagem_path, prompt)
            resultado.clip = clip
            
            if clip < limiares.get("clip", 0.32):
                resultado.erros.append(f"CLIP={clip:.3f}")
        
        # 4. Qualidade de Rostos
        tem_rosto, face_quality = self._avaliar_rosto(imagem_path)
        resultado.tem_rosto = tem_rosto
        resultado.face_quality = face_quality
        
        if tem_rosto and ("pessoa" in prompt_lower or "rosto" in prompt_lower or "face" in prompt_lower or "retrato" in prompt_lower):
            if face_quality > limiares.get("face_quality", 0.3):
                resultado.erros.append(f"Rosto={face_quality:.2f}")
        
        # Decisão final
        resultado.aprovada = len(resultado.erros) == 0
        
        if resultado.aprovada:
            resultado.mensagem = "✅ Aprovada"
        else:
            resultado.mensagem = f"❌ Reprovada: {'; '.join(resultado.erros)}"
        
        return resultado
    
    def avaliar_batch(self, lista_imagens: List[Tuple[str, str]]) -> List[ResultadoAvaliacao]:
        """Avalia múltiplas imagens."""
        resultados = []
        
        for caminho, prompt in lista_imagens:
            resultado = self.avaliar_imagem(caminho, prompt)
            resultados.append(resultado)
            
            status = "✅" if resultado.aprovada else "❌"
            print(f"{status} {os.path.basename(caminho)}: {resultado.mensagem}")
        
        self.resultados = resultados
        return resultados
    
    def obter_aprovadas(self) -> List[str]:
        """Retorna lista de imagens aprovadas."""
        return [r for r in self.resultados if r.aprovada]
    
    def obter_rejeitadas(self) -> List[str]:
        """Retorna lista de imagens rejeitadas."""
        return [r for r in self.resultados if not r.aprovada]
    
    def limpar(self):
        """Libera memória dos modelos."""
        if self.modelo_clip is not None:
            del self.modelo_clip
            self.modelo_clip = None
        
        gc.collect()
        if torch:
            torch.cuda.empty_cache()