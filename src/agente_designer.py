#!/usr/bin/env python3
"""
Agente Designer (Artista Digital)
Gera imagens usando SDXL-Turbo, Flux.1 Schnell ou SDXL baseado no modo.
Otimizado para GPU T4 do Colab.
"""

import gc
import os
import random
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Imports para produção
# import torch
# from diffusers import StableDiffusionXLPipeline, FluxPipeline


class ModoDesigner(Enum):
    """Modos de operação do Designer."""
    BASIC = "basic"       # SDXL-Turbo 768x768, ~5-10s
    PROFISSIONAL = "pro"   # Flux.1 Schnell 1024x1024, ~30-40s
    PORTFOLIO = "portfolio"  # Flux.1 Schnell 1024x1024, rigoroso


class AgenteDesigner:
    """Agente que gera imagens a partir de prompts."""
    
    # Modelos disponíveis
    MODELO_SDXL_TURBO = "stabilityai/sdxl-turbo"
    MODELO_FLUX_SCHNELL = "black-forest-labs/FLUX.1-schnell"
    MODELO_SDXL = "stabilityai/stable-diffusion-xl-base-1.0"
    
    # Resoluções por modo
    RESOLUCOES = {
        ModoDesigner.BASIC: (768, 768),
        ModoDesigner.PROFISSIONAL: (1024, 1024),
        ModoDesigner.PORTFOLIO: (1024, 1024)
    }
    
    def __init__(self, pasta_projeto: Optional[Path] = None, modo: str = "basic"):
        self.pasta_projeto = pasta_projeto
        self.modo = ModoDesigner(modo) if modo in [m.value for m in ModoDesigner] else ModoDesigner.BASIC
        self.pipeline = None
        self.device = None
        self.modelo_usado = None
        
        # LoRAs carregados (Modo Profissional)
        self.loras = {}
    
    def _verificar_vram(self) -> int:
        """Verifica VRAM usada em MB."""
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True
            )
            return int(result.stdout.decode().strip())
        except:
            return 0
    
    def _verificar_disponibilidade_vram(self, min_vram_mb: int = 14000) -> bool:
        """Verifica se há VRAM suficiente disponível."""
        vram_usado = self._verificar_vram()
        vram_livre = 15000 - vram_usado  # T4 tem ~15GB
        return vram_livre >= min_vram_mb
    
    def _obter_modelo(self) -> str:
        """Retorna o modelo baseado no modo."""
        if self.modo == ModoDesigner.BASIC:
            return self.MODELO_SDXL_TURBO
        elif self.modo == ModoDesigner.PROFISSIONAL:
            return self.MODELO_FLUX_SCHNELL
        elif self.modo == ModoDesigner.PORTFOLIO:
            return self.MODELO_FLUX_SCHNELL
        return self.MODELO_SDXL_TURBO
    
    def _obter_resolucao(self) -> Tuple[int, int]:
        """Retorna a resolução baseada no modo."""
        return self.RESOLUCOES.get(self.modo, (768, 768))
    
    def _inicializar_pipeline(
        self, 
        modelo: Optional[str] = None,
        cache_dir: Optional[str] = None
    ) -> Any:
        """Inicializa o pipeline do modelo selecionado."""
        if modelo is None:
            modelo = self._obter_modelo()
        
        if not self._verificar_disponibilidade_vram():
            raise RuntimeError(
                "VRAM insuficiente. Considere reiniciar o ambiente Colab."
            )
        
        # Código real (descomentar em produção com GPU)
        # config = {"torch_dtype": torch.bfloat16}
        # if cache_dir:
        #     config["cache_dir"] = cache_dir
        # 
        # if "sdxl" in modelo.lower():
        #     self.pipeline = StableDiffusionXLPipeline.from_pretrained(modelo, **config)
        # else:
        #     self.pipeline = FluxPipeline.from_pretrained(modelo, **config)
        # 
        # self.pipeline.enable_attention_slicing()
        # self.pipeline.enable_vae_slicing()
        # 
        # if torch.cuda.is_available():
        #     self.pipeline.to("cuda")
        #     self.device = "cuda"
        
        self.pipeline = "mock_pipeline"
        self.modelo_usado = modelo
        return self.pipeline
    
    def _liberar_memoria(self) -> None:
        """Libera memória da GPU."""
        if self.pipeline:
            del self.pipeline
        self.pipeline = None
        
        try:
            import torch
            torch.cuda.empty_cache()
        except:
            pass
        gc.collect()
    
    def carregar_lora(self, nome: str, caminho: str, escala: float = 1.0) -> None:
        """Carrega um LoRA (Modo Profissional)."""
        # Código real
        # self.pipeline.load_lora_weights(caminho)
        # self.loras[nome] = {"caminho": caminho, "escala": escala}
        
        self.loras[nome] = {"caminho": caminho, "escala": escala}
    
    def gerar_imagem(
        self, 
        prompt: str,
        formato: str = "feed",
        seed: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        altura: Optional[int] = None,
        largura: Optional[int] = None,
        negativo: Optional[str] = None
    ) -> Tuple[Path, int]:
        """
        Gera uma imagem a partir do prompt.
        
        Args:
            prompt: Texto do prompt
            formato: Formato da imagem
            seed: Seed aleatório
            num_inference_steps: Passos de inferência
            guidance_scale: Guidance scale
            altura: Altura customizada
            largura: Largura customizada
            negativo: Prompt negativo
            
        Returns:
            Tupla (caminho_da_imagem, seed_usado)
        """
        if seed is None:
            seed = random.randint(0, 999999)
        
        # Resolução
        if altura is None or largura is None:
            altura, largura = self._obter_resolucao()
        
        # Parâmetros por modo
        if num_inference_steps is None:
            if self.modo == ModoDesigner.BASIC:
                num_inference_steps = 4  # Turbo
            elif self.modo == ModoDesigner.PROFISSIONAL:
                num_inference_steps = 4  # Schnell
            else:
                num_inference_steps = 4
        
        if guidance_scale is None:
            if self.modo == ModoDesigner.BASIC:
                guidance_scale = 0.0  # Turbo
            else:
                guidance_scale = 3.5
        
        if negativo is None:
            negativo = "low quality, blurry, ugly, deformed"
        
        # Gerar imagem (código real descomentar em produção)
        # generator = torch.Generator(device=self.device).manual_seed(seed)
        # imagem = self.pipeline(
        #     prompt=prompt,
        #     negative_prompt=negativo,
        #     num_inference_steps=num_inference_steps,
        #     guidance_scale=guidance_scale,
        #     height=altura,
        #     width=largura,
        #     generator=generator
        # ).images[0]
        
        # Modo mock: criar imagem placeholder
        imagem = self._criar_imagem_mock(altura, largura, seed)
        
        # Salvar imagem
        caminho = self._salvar_imagem(imagem, seed)
        
        return caminho, seed
    
    def _criar_imagem_mock(self, altura: int, largura: int, seed: int) -> Any:
        """Cria uma imagem mock para testes."""
        try:
            from PIL import Image, ImageDraw
            
            random.seed(seed)
            r = random.randint(50, 200)
            g = random.randint(50, 200)
            b = random.randint(50, 200)
            
            img = Image.new('RGB', (largura, altura), (r, g, b))
            draw = ImageDraw.Draw(img)
            
            for i in range(5):
                x1 = random.randint(0, largura)
                y1 = random.randint(0, altura)
                x2 = random.randint(0, largura)
                y2 = random.randint(0, altura)
                cor = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                draw.rectangle([x1, y1, x2, y2], outline=cor, width=3)
            
            return img
        except ImportError:
            return {"mock": True, "altura": altura, "largura": largura, "seed": seed}
    
    def _salvar_imagem(self, imagem: Any, seed: int) -> Path:
        """Salva a imagem em arquivo."""
        pasta_temp = self.pasta_projeto / "imagens_temp" if self.pasta_projeto else Path("imagens_temp")
        pasta_temp.mkdir(parents=True, exist_ok=True)
        
        caminho = pasta_temp / f"imagem_{seed}.png"
        
        if hasattr(imagem, 'save'):
            imagem.save(caminho)
        else:
            caminho.touch()
        
        return caminho
    
    def gerar_variacoes(
        self, 
        prompt: str,
        num_variacoes: int = 4,
        formato: str = "feed",
        max_tentativas: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Gera múltiplas variações de uma imagem.
        
        Args:
            prompt: Prompt base
            num_variacoes: Número de variações
            formato: Formato da imagem
            max_tentativas: Máximo de tentativas
            
        Returns:
            Lista de resultados
        """
        resultados = []
        
        for i in range(num_variacoes):
            seed = random.randint(0, 999999)
            
            try:
                caminho, seed_usado = self.gerar_imagem(
                    prompt=prompt,
                    formato=formato,
                    seed=seed
                )
                
                resultados.append({
                    "caminho": str(caminho),
                    "seed": seed_usado,
                    "sucesso": True,
                    "indice": i + 1
                })
            except Exception as e:
                resultados.append({
                    "caminho": None,
                    "seed": seed,
                    "sucesso": False,
                    "erro": str(e),
                    "indice": i + 1
                })
        
        return resultados
    
    def mover_para_aprovadas(self, caminho: Path, pasta_aprovadas: Optional[Path] = None) -> Path:
        """Move imagem para pasta de aprovadas."""
        if pasta_aprovadas is None:
            pasta_aprovadas = self.pasta_projeto / "aprovadas" if self.pasta_projeto else Path("imagens_aprovadas")
        pasta_aprovadas.mkdir(parents=True, exist_ok=True)
        
        nome = caminho.name
        caminho_destino = pasta_aprovadas / nome
        
        import shutil
        shutil.move(str(caminho), str(caminho_destino))
        
        return caminho_destino
    
    def mover_para_rascunho(self, caminho: Path, pasta_rascunho: Optional[Path] = None) -> Path:
        """Move imagem para pasta de rascunho."""
        if pasta_rascunho is None:
            pasta_rascunho = self.pasta_projeto / "rascunho" if self.pasta_projeto else Path("imagens_rascunho")
        pasta_rascunho.mkdir(parents=True, exist_ok=True)
        
        nome = caminho.name
        caminho_destino = pasta_rascunho / nome
        
        import shutil
        shutil.move(str(caminho), str(caminho_destino))
        
        return caminho_destino
    
    def limpar_temp(self) -> None:
        """Limpa imagens temporárias."""
        if self.pasta_projeto:
            pasta_temp = self.pasta_projeto / "imagens_temp"
            if pasta_temp.exists():
                import shutil
                shutil.rmtree(pasta_temp)
                pasta_temp.mkdir()
    
    def get_modo(self) -> str:
        """Retorna o modo atual."""
        return self.modo.value
    
    def set_modo(self, modo: str) -> None:
        """Define o modo de operação."""
        self.modo = ModoDesigner(modo)