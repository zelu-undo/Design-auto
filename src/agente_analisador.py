#!/usr/bin/env python3
"""
Agente Analisador de Estilo
Extrai paleta de cores, estilos tipográficos, iluminação e mood das imagens de referência.
Usa transformers + bitsandbytes (quantização 4-bit), sem Ollama.
"""

import gc
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Imports para uso local (em produção)
try:
    import torch
    from transformers import AutoProcessor, LlavaForConditionalGeneration
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    TORCH_DISPONIVEL = True
except ImportError:
    TORCH_DISPONIVEL = False
    torch = None
    AutoProcessor = None
    LlavaForConditionalGeneration = None
    AutoModelForCausalLM = None
    BitsAndBytesConfig = None


class AgenteAnalisador:
    """Agente que analisa referências visuais e textuais para gerar um Style Guide."""
    
    # Modelo para análise de imagens (Qwen2.5-VL é melhor que LLaVA)
    MODELO_QWEN = "Qwen/Qwen2.5-VL-7B-Instruct"
    MODELO_LLAVA_16 = "llava-hf/llava-v1.6-mistral-7b-hf"
    MODELO_GEMMA = "google/gemma-2-9b-it"  # Fallback para texto
    
    def __init__(self, pasta_projeto: Optional[Path] = None):
        self.pasta_projeto = pasta_projeto
        self.modelo_selecionado = None
        self.pipeline = None
        self.device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
    
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
    
    def _verificar_disponibilidade_vram(self, min_vram_mb: int = 5000) -> bool:
        """Verifica se há VRAM suficiente disponível."""
        vram_usado = self._verificar_vram()
        vram_livre = 15000 - vram_usado  # T4 tem ~15GB
        return vram_livre >= min_vram_mb
    
    def _carregar_modelo_imagem(
        self, 
        modelo: str = "llava-hf/llava-1.5-7b-hf",
        cache_dir: Optional[str] = None
    ) -> Any:
        """Carrega o modelo LLaVA com quantização 4-bit."""
        if not self._verificar_disponibilidade_vram(5000):
            raise RuntimeError(
                "VRAM insuficiente para carregar LLaVA. Considere reiniciar o ambiente Colab."
            )
        
        # Código real (descomentar em produção com GPU)
        # config = BitsAndBytesConfig(
        #     load_in_4bit=True,
        #     bnb_4bit_quant_type="nf4",
        #     bnb_4bit_compute_dtype=torch.bfloat16,
        #     bnb_4bit_use_double_quant=True
        # )
        # 
        # if cache_dir:
        #     self.pipeline = AutoProcessor.from_pretrained(
        #         modelo, 
        #         cache_dir=cache_dir
        #     )
        #     self.modelo = LlavaForConditionalGeneration.from_pretrained(
        #         modelo,
        #         quantization_config=config,
        #         device_map="auto",
        #         cache_dir=cache_dir
        #     )
        # else:
        #     self.pipeline = AutoProcessor.from_pretrained(modelo)
        #     self.modelo = LlavaForConditionalGeneration.from_pretrained(
        #         modelo,
        #         quantization_config=config,
        #         device_map="auto"
        #     )
        
        self.pipeline = "mock_llava"
        self.modelo = "mock_model"
        return self.pipeline
    
    def _carregar_modelo_texto(
        self, 
        modelo: str = "google/gemma-2-9b-it",
        cache_dir: Optional[str] = None
    ) -> Any:
        """Carrega o modelo Gemma com quantização 4-bit."""
        if not self._verificar_disponibilidade_vram(6000):
            raise RuntimeError(
                "VRAM insuficiente para carregar Gemma. Considere reiniciar o ambiente Colab."
            )
        
        # Código real (descomentar em produção com GPU)
        # config = BitsAndBytesConfig(
        #     load_in_4bit=True,
        #     bnb_4bit_quant_type="nf4",
        #     bnb_4bit_compute_dtype=torch.bfloat16,
        #     bnb_4bit_use_double_quant=True
        # )
        # 
        # if cache_dir:
        #     self.modelo = AutoModelForCausalLM.from_pretrained(
        #         modelo,
        #         quantization_config=config,
        #         device_map="auto",
        #         cache_dir=cache_dir
        #     )
        # else:
        #     self.modelo = AutoModelForCausalLM.from_pretrained(
        #         modelo,
        #         quantization_config=config,
        #         device_map="auto"
        #     )
        # 
        # self.processor = AutoTokenizer.from_pretrained(modelo)
        
        self.modelo = "mock_gemma"
        self.pipeline = "mock_tokenizer"
        return self.modelo
    
    def _descarregar_modelo(self) -> None:
        """Descarrega o modelo da memória."""
        if hasattr(self, 'modelo') and self.modelo:
            del self.modelo
        if hasattr(self, 'pipeline') and self.pipeline:
            del self.pipeline
        
        self.modelo = None
        self.pipeline = None
        
        try:
            import torch
            torch.cuda.empty_cache()
        except:
            pass
        gc.collect()
    
    def _construir_prompt_analise(self, briefing: str, imagens_paths: Optional[List[str]] = None) -> str:
        """Constrói o prompt para análise do modelo."""
        base_prompt = """Analise as imagens de referência fornecidas e gere um Style Guide estruturado em JSON com os seguintes campos:
{
    "paleta_cores": {
        "principais": ["#codigohex1", "#codigohex2", ...],
        "secundarias": ["#codigohex1", ...],
        "acentos": ["#codigohex1", ...],
        "descricao": "descrição textual das cores predominantes e seu uso"
    },
    "tipografia": {
        "familias": ["nome da fonte 1", "nome da fonte 2"],
        "usos": {"cabeçalhos": "fonte1", "corpo": "fonte2"},
        "descricao": "características gerais da tipografia"
    },
    "iluminacao": {
        "tipo": "direta/indireta/mista",
        "temperatura": "quente/fria/neutra",
        "contraste": "alto/medio/baixo",
        "descricao": "descrição da iluminação"
    },
    "composicao": {
        "estilo": "minimalista/detalhado/geometrico/organico",
        "regra_tercos": true/false,
        "espaco_negativo": "much/little/balanced",
        "descricao": "descrição da composição"
    },
    "mood": {
        "palavras_chave": ["palavra1", "palavra2", ...],
        "emoções": ["emoção1", "emoção2", ...],
        "referencias_visuais": ["referencia1", ...],
        "descricao": "descrição do mood geral"
    },
    "elementos_visuais": {
        "formatos": ["formato1", ...],
        "padrões": ["padrão1", ...],
        "texturas": ["textura1", ...],
        "descricao": "descrição dos elementos"
    }
}"""
        
        if briefing:
            base_prompt += f"\n\nBriefing fornecido: {briefing}"
        
        if imagens_paths:
            base_prompt += f"\n\nImagens de referência fornecidas: {len(imagens_paths)} imagens"
        
        return base_prompt
    
    def _parsear_resposta_json(self, resposta: str) -> Dict[str, Any]:
        """Extrai JSON da resposta do modelo."""
        # Tenta encontrar bloco JSON na resposta
        inicio = resposta.find('{')
        fim = resposta.rfind('}')
        
        if inicio != -1 and fim != -1:
            json_str = resposta[inicio:fim+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Se não conseguir parsear, retorna estrutura vazia
        return {
            "paleta_cores": {"principais": [], "secundarias": [], "acentos": [], "descricao": ""},
            "tipografia": {"familias": [], "usos": {}, "descricao": ""},
            "iluminacao": {"tipo": "", "temperatura": "", "contraste": "", "descricao": ""},
            "composicao": {"estilo": "", "regra_tercos": False, "espaco_negativo": "", "descricao": ""},
            "mood": {"palavras_chave": [], "emoções": [], "referencias_visuais": [], "descricao": ""},
            "elementos_visuais": {"formatos": [], "padrões": [], "texturas": [], "descricao": ""}
        }
    
    def analisar_com_modelo(
        self, 
        briefing: str, 
        imagens_paths: Optional[List[str]] = None,
        modo_texto_apenas: bool = False
    ) -> Dict[str, Any]:
        """Executa a análise usando transformers."""
        # Selecionar modelo
        if imagens_paths and not modo_texto_apenas:
            modelo = self.MODELO_LLAVA_15
        else:
            modelo = self.MODELO_GEMMA
        
        self.modelo_selecionado = modelo
        
        # Carregar modelo
        if imagens_paths and not modo_texto_apenas:
            self._carregar_modelo_imagem(modelo)
        else:
            self._carregar_modelo_texto(modelo)
        
        # Construir prompt
        prompt_sistema = self._construir_prompt_analise(briefing, imagens_paths)
        
        # Código real (descomentar em produção)
        # if imagens_paths and not modo_texto_apenas:
        #     # Modo multimodal
        #     from PIL import Image
        #     imagens = [Image.open(p) for p in imagens_paths]
        #     inputs = self.pipeline(
        #         prompt_sistema,
        #         images=imagens,
        #         return_tensors="pt"
        #     ).to(self.device)
        #     
        #     with torch.no_grad():
        #         output = self.modelo.generate(**inputs, max_new_tokens=500)
        #     resposta = self.pipeline.decode(output[0], skip_special_tokens=True)
        # else:
        #     # Modo texto apenas
        #     inputs = self.processor(prompt_sistema, return_tensors="pt").to(self.device)
        #     
        #     with torch.no_grad():
        #         output = self.modelo.generate(**inputs, max_new_tokens=500)
        #     resposta = self.processor.decode(output[0], skip_special_tokens=True)
        
        # Mock: retornar resultado
        resposta = "Mock response"
        
        # Descarregar modelo
        self._descarregar_modelo()
        
        return self._parsear_resposta_json(resposta)
    
    def analisar_mock(
        self, 
        briefing: str, 
        imagens_paths: Optional[List[str]] = None,
        modo_texto_apenas: bool = False
    ) -> Dict[str, Any]:
        """
        Versão mock para testes sem GPU.
        Retorna um Style Guide示例 com valores predefinidos.
        """
        # Selecionar modelo simulado
        if imagens_paths and not modo_texto_apenas:
            self.modelo_selecionado = self.MODELO_LLAVA_15
        else:
            self.modelo_selecionado = self.MODELO_GEMMA
        
        # Retornar exemplo baseado no briefing
        if "moda" in briefing.lower() or "fashion" in briefing.lower():
            return {
                "paleta_cores": {
                    "principais": ["#1A1A2E", "#C4A77D", "#E8E8E8"],
                    "secundarias": ["#8B8B8B", "#2F2F2F"],
                    "acentos": ["#D4AF37"],
                    "descricao": "Cores elegantes e sofisticadas, predominância de tons escuros com accent dourado"
                },
                "tipografia": {
                    "familias": ["Playfair Display", "Lato"],
                    "usos": {"cabeçalhos": "Playfair Display", "corpo": "Lato"},
                    "descricao": "Serif elegante para títulos, sans-serif discreta para texto"
                },
                "iluminacao": {
                    "tipo": "indireta",
                    "temperatura": "quente",
                    "contraste": "medio",
                    "descricao": "Iluminação suave e difusa, destaque para texturas"
                },
                "composicao": {
                    "estilo": "minimalista",
                    "regra_tercos": True,
                    "espaco_negativo": "balanced",
                    "descricao": "Composição limpa com espaço negativo equilibrado"
                },
                "mood": {
                    "palavras_chave": ["elegante", "minimal", "sofisticado", "chic"],
                    "emoções": ["confiança", "sofisticação"],
                    "referencias_visuais": ["vogue", "runway"],
                    "descricao": "Mood elegante e atemporal"
                },
                "elementos_visuais": {
                    "formatos": ["retrato", "full body"],
                    "padrões": ["solid", "textura_fina"],
                    "texturas": ["tecido", "couro"],
                    "descricao": "Foco em texturas e materiais de qualidade"
                }
            }
        elif "tecnologia" in briefing.lower() or "tech" in briefing.lower():
            return {
                "paleta_cores": {
                    "principais": ["#0A0A0A", "#00D4FF", "#FFFFFF"],
                    "secundarias": ["#1E1E1E", "#2D2D2D"],
                    "acentos": ["#00FF88"],
                    "descricao": "Cores tecnológicas, fundo escuro com accent cibernético"
                },
                "tipografia": {
                    "familias": ["Inter", "Roboto Mono"],
                    "usos": {"cabeçalhos": "Inter", "corpo": "Roboto Mono"},
                    "descricao": "Fontes limpas e técnicas"
                },
                "iluminacao": {
                    "tipo": "mista",
                    "temperatura": "fria",
                    "contraste": "alto",
                    "descricao": "Alto contraste com luz fria"
                },
                "composicao": {
                    "estilo": "geometrico",
                    "regra_tercos": True,
                    "espaco_negativo": "little",
                    "descricao": "Composição densa e informativa"
                },
                "mood": {
                    "palavras_chave": ["futurista", "limpo", "innovador", "tecnológico"],
                    "emoções": ["innovação", "precisão"],
                    "referencias_visuais": ["cyberpunk", "ui_design"],
                    "descricao": "Mood tecnológico e inovador"
                },
                "elementos_visuais": {
                    "formatos": ["interface", "dashboard"],
                    "padrões": ["grid", "geometricos"],
                    "texturas": ["glassmorphism", "gradiente"],
                    "descricao": "Elementos UI modernos"
                }
            }
        else:
            # Default genérico
            return {
                "paleta_cores": {
                    "principais": ["#2C3E50", "#E74C3C", "#ECF0F1"],
                    "secundarias": ["#3498DB", "#95A5A6"],
                    "acentos": ["#F39C12"],
                    "descricao": "Cores balanceadas, tons azul escuro com accent vibrante"
                },
                "tipografia": {
                    "familias": ["Montserrat", "Open Sans"],
                    "usos": {"cabeçalhos": "Montserrat", "corpo": "Open Sans"},
                    "descricao": "Fontes modernas e legíveis"
                },
                "iluminacao": {
                    "tipo": "mista",
                    "temperatura": "neutra",
                    "contraste": "medio",
                    "descricao": "Iluminação natural e equilibrada"
                },
                "composicao": {
                    "estilo": "organico",
                    "regra_tercos": True,
                    "espaco_negativo": "balanced",
                    "descricao": "Composição natural e equilibrada"
                },
                "mood": {
                    "palavras_chave": ["profissional", "moderno", "clean"],
                    "emoções": ["confiança", "claridade"],
                    "referencias_visuais": ["corporativo", "branding"],
                    "descricao": "Mood profissional e moderno"
                },
                "elementos_visuais": {
                    "formatos": ["feed", "story"],
                    "padrões": ["minimal", "solid"],
                    "texturas": ["smooth"],
                    "descricao": "Elementos limpos e sofisticados"
                }
            }
    
    def analisar(
        self, 
        briefing: str, 
        imagens_paths: Optional[List[str]] = None,
        modo_texto_apenas: bool = False,
        usar_modelo_real: bool = False,
        cache_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Método principal de análise.
        
        Args:
            briefing: Texto com o briefing do projeto
            imagens_paths: Lista de caminhos para imagens de referência
            modo_texto_apenas: Force modo texto (sem análise de imagem)
            usar_modelo_real: Usar modelos reais ( requer GPU)
            cache_dir: Diretório de cache dos modelos
            
        Returns:
            Style Guide em formato Dict
        """
        if usar_modelo_real:
            return self.analisar_com_modelo(
                briefing, 
                imagens_paths, 
                modo_texto_apenas
            )
        else:
            return self.analisar_mock(
                briefing, 
                imagens_paths, 
                modo_texto_apenas
            )
    
    def salvar_style_guide(self, style_guide: Dict[str, Any], caminho: Optional[Path] = None) -> Path:
        """Salva o Style Guide em arquivo JSON."""
        if caminho is None and self.pasta_projeto:
            caminho = self.pasta_projeto / "style_guide.json"
        
        if caminho:
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(style_guide, f, indent=2, ensure_ascii=False)
            return caminho
        
        raise ValueError("Caminho não especificado e pasta_projeto não definida")
    
    @staticmethod
    def carregar_style_guide(caminho: Path) -> Dict[str, Any]:
        """Carrega um Style Guide de arquivo."""
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def gerar_prompt_imagem(style_guide: Dict[str, Any], tipo: str = "feed") -> str:
        """
        Gera um prompt base para geração de imagem a partir do Style Guide.
        
        Args:
            style_guide: O Style Guide extraído
            tipo: Tipo de imagem (feed, story, banner)
            
        Returns:
            Prompt textual para geração de imagem
        """
        # Extrair elementos do Style Guide
        paleta = style_guide.get("paleta_cores", {})
        tipografia = style_guide.get("tipografia", {})
        iluminacao = style_guide.get("iluminacao", {})
        composicao = style_guide.get("composicao", {})
        mood = style_guide.get("mood", {})
        
        # Construir prompt base
        prompt_parts = []
        
        # Adicionar mood
        if mood.get("palavras_chave"):
            prompt_parts.extend(mood["palavras_chave"])
        
        # Adicionar descrição visual
        if iluminacao.get("descricao"):
            prompt_parts.append(iluminacao["descricao"])
        
        if composicao.get("descricao"):
            prompt_parts.append(composicao["descricao"])
        
        # Adicionar paleta de cores
        if paleta.get("principais"):
            cores = ", ".join(paleta["principais"][:3])
            prompt_parts.append(f"color palette: {cores}")
        
        # Adicionar elementos visuais
        elementos = style_guide.get("elementos_visuais", {})
        if elementos.get("formatos"):
            prompt_parts.append(f"format: {', '.join(elementos['formatos'])}")
        
        return ", ".join(prompt_parts)