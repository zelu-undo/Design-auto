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

# Imports para produção (com fallback)
try:
    import torch
    from diffusers import StableDiffusionXLPipeline, FluxPipeline
    TORCH_DISPONIVEL = True
except ImportError:
    TORCH_DISPONIVEL = False
    torch = None
    StableDiffusionXLPipeline = None
    FluxPipeline = None


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
        
        # Verificar se torch está disponível
        if not TORCH_DISPONIVEL:
            raise RuntimeError(
                "PyTorch não está instalado. Execute: pip install torch diffusers"
            )
        
        if not self._verificar_disponibilidade_vram():
            raise RuntimeError(
                "VRAM insuficiente. Considere reiniciar o ambiente Colab."
            )
        
        # Carregar modelo real
        config = {"torch_dtype": torch.bfloat16}
        if cache_dir:
            config["cache_dir"] = cache_dir
        
        if "sdxl" in modelo.lower():
            self.pipeline = StableDiffusionXLPipeline.from_pretrained(modelo, **config)
        else:
            self.pipeline = FluxPipeline.from_pretrained(modelo, **config)
        
        self.pipeline.enable_attention_slicing()
        self.pipeline.enable_vae_slicing()
        
        if torch.cuda.is_available():
            self.pipeline.to("cuda")
            self.device = "cuda"
        
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
            negativo = "low quality, blurry, ugly, deformed, watermark, signature"
        
        # Gerar imagem usando IA real
        if TORCH_DISPONIVEL and self.pipeline and hasattr(self.pipeline, '__call__'):
            generator = torch.Generator(device=self.device).manual_seed(seed)
            imagem = self.pipeline(
                prompt=prompt,
                negative_prompt=negativo,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                height=altura,
                width=largura,
                generator=generator
            ).images[0]
        else:
            # Pipeline não disponível (sem GPU) - usar fallback
            raise RuntimeError("Pipeline não inicializado. Execute em ambiente com GPU.")
        
        # Salvar imagem
        caminho = self._salvar_imagem(imagem, seed)
        
        return caminho, seed
    
    def _criar_imagem_mock(self, altura: int, largura: int, seed: int) -> Any:
        """Cria uma imagem mock (apenas se não houver GPU)."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            
            random.seed(seed)
            
            # Cor de fundo baseada no seed (azul/acinzentado para logo/logística)
            cores_fundo = [
                (45, 85, 145),    # Azul profissional
                (52, 73, 94),    # Azul escuro
                (236, 240, 241), # Cinza claro
                (44, 62, 80),    # Azul noite
                (231, 76, 60),  # Vermelho accent
            ]
            cor_fundo = cores_fundo[seed % len(cores_fundo)]
            
            img = Image.new('RGB', (largura, altura), cor_fundo)
            draw = ImageDraw.Draw(img)
            
            # Adicionar elementos visuais mais elaborados
            # Linhas horizontais (estilo logo)
            num_linhas = random.randint(2, 5)
            for i in range(num_linhas):
                y = altura // (num_linhas + 1) * (i + 1)
                espessura = random.randint(3, 15)
                cor_linha = (255, 255, 255) if sum(cor_fundo) < 300 else (0, 0, 0)
                draw.line([(0, y), (largura, y)], fill=cor_linha, width=espessura)
            
            # Circunferência (ícone)
            centro_x, centro_y = largura // 2, altura // 2
            raio = min(largura, altura) // 4
            cor_accent = (255, 255, 255) if sum(cor_fundo) < 300 else (231, 76, 60)
            draw.ellipse([
                centro_x - raio,
                centro_y - raio,
                centro_x + raio,
                centro_y + raio
            ], outline=cor_accent, width=8)
            
            # Texto (se suportado)
            try:
                # Tentar adicionar texto simplificado
                draw.text(
                    (largura // 2, altura - 30),
                    "ARTISAN",
                    fill=cor_accent
                )
            except:
                pass
            
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