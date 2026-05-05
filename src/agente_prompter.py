#!/usr/bin/env python3
"""
Agente Prompter (Diretor de Arte)
Converte o guia de estilo em prompts profissionais para geração de imagens.
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

# Imports para uso local (em produção)
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TORCH_DISPONIVEL = True
except ImportError:
    TORCH_DISPONIVEL = False
    torch = None
    AutoModelForCausalLM = None
    AutoTokenizer = None


class AgentePrompter:
    """Agente que gera prompts profissionais a partir do Style Guide."""
    
    # Modelo para geração de prompts (Phi-3 é melhor que GPT-2)
    MODELO_PHI3 = "microsoft/Phi-3-mini-4k-instruct"
    MODELO_LLAMA = "meta-llama/Llama-3.2-3B"
    
    def __init__(self, pasta_projeto: Optional[Path] = None):
        self.pasta_projeto = pasta_projeto
        self.modelo_selecionado = None
    
    def _construir_prompt_geracao(self, style_guide: Dict[str, Any], num_prompts: int = 10) -> str:
        """Constrói o prompt para geração de prompts de imagem."""
        
        prompt_sistema = f"""A partir do Style Guide fornecido, gere exatamente {num_prompts} prompts professionais para geração de imagens.
Cada prompt deve ter os seguintes campos:
- "prompt": texto completo do prompt para FLUX ou similar
- "formato": "feed" ou "story" ou "banner"
- "seed": número aleatório (opcional)
- "variacao": número indicando variação (1, 2, ou 3)
- "descricao": breve descrição do que a imagem deve conter

O formato JSON esperado é uma lista de objetos assim:
[
    {{
        "prompt": "texto do prompt...",
        "formato": "feed",
        "seed": 12345,
        "variacao": 1,
        "descricao": "descrição breve"
    }},
    ...
]

O prompt deve:
1. Ser detalhado e específico
2. Incluir referências de estilo (Lighting, composition, style)
3. Usar termos de arte digital profissional
4. Ser apropriado para FLUX ou modelos similares
5. Variar entre diferentes composições e enquadramentos

Retorne apenas o JSON, sem texto adicional."""
        
        # Adicionar informações do Style Guide
        guide_json = json.dumps(style_guide, indent=2, ensure_ascii=False)
        prompt_completo = f"{prompt_sistema}\n\nStyle Guide:\n{guide_json}"
        
        return prompt_completo
    
    def _parsear_resposta_json(self, resposta: str) -> List[Dict[str, Any]]:
        """Extrai lista de prompts da resposta do modelo."""
        inicio = resposta.find('[')
        fim = resposta.rfind(']')
        
        if inicio != -1 and fim != -1:
            json_str = resposta[inicio:fim+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Tentar com objetos individuais
        objetos = []
        inicio = resposta.find('{')
        while inicio != -1:
            fim = resposta.find('}', inicio)
            if fim == -1:
                break
            obj_str = resposta[inicio:fim+1]
            try:
                objetos.append(json.loads(obj_str))
            except:
                pass
            inicio = resposta.find('{', fim)
        
        return objetos
    
    def gerar_com_ollama(self, style_guide: Dict[str, Any], num_prompts: int = 10) -> List[Dict[str, Any]]:
        """Gera prompts usando Ollama (Gemma 2)."""
        self.modelo_selecionado = self.MODELO_GEMMA
        
        prompt_sistema = self._construir_prompt_geracao(style_guide, num_prompts)
        
        resposta = ollama.chat(
            model=self.MODELO_GEMMA,
            messages=[{'role': 'user', 'content': prompt_sistema}]
        )
        
        texto_resposta = resposta['message']['content']
        prompts = self._parsear_resposta_json(texto_resposta)
        
        # Adicionar campos default se necessário
        for p in prompts:
            if 'processado' not in p:
                p['processado'] = False
            if 'aprovado' not in p:
                p['aprovado'] = False
            if 'seed' not in p:
                p['seed'] = random.randint(0, 999999)
        
        return prompts
    
    def gerar_mock(
        self, 
        style_guide: Dict[str, Any],
        num_prompts: int = 10,
        formato_base: str = "feed"
    ) -> List[Dict[str, Any]]:
        """Gera prompts mock para testes."""
        self.modelo_selecionado = self.MODELO_GEMMA
        
        # Extrair elementos do style guide
        paleta = style_guide.get("paleta_cores", {})
        tipografia = style_guide.get("tipografia", {})
        mood = style_guide.get("mood", {})
        elementos = style_guide.get("elementos_visuais", {})
        
        # Cores principais
        cores = paleta.get("principais", ["#2C3E50", "#E74C3C"])
        cores_str = ", ".join(cores[:3])
        
        # Palavras-chave do mood
        palavras_mood = mood.get("palavras_chave", ["modern", "professional"])
        mood_str = ", ".join(palavras_mood[:3])
        
        # Elementos visuais
        formatos = elementos.get("formatos", ["feed"])
        
        # Gerar prompts baseados no tipo
        prompts = []
        
        templates_feed = [
            "{mood}, {cores} color palette, professional {formato}, soft lighting, high quality, detailed",
            "Modern {mood} aesthetic, {cores}, minimalist composition, natural light, 4k, photorealistic",
            "{mood} style artwork, cohesive {cores} palette, dynamic composition, studio lighting",
            "Professional {formato} design, {cores}, clean background, soft shadows, premium feel",
            "{mood} brand imagery, {cores}, geometric shapes, balanced composition, elegant"
        ]
        
        templates_story = [
            "{mood} story moment, {cores} gradient background, texturable, engaging",
            "Vertical {formato}, {cores}, centered subject, mobile optimized",
            "{mood} narrative scene, {cores}, compelling composition"
        ]
        
        templates_banner = [
            "{mood} banner, {cores}, wide format, professional, horizontal layout",
            "Web {formato}, {cores}, clean design, modern typography space",
            "{mood} hero image, {cores}, full width, impactful"
        ]
        
        # Selecionar templates baseado no formato base
        if formato_base == "story":
            templates = templates_story
        elif formato_base == "banner":
            templates = templates_banner
        else:
            templates = templates_feed
        
        # Gerar variações
        for i in range(num_prompts):
            template = random.choice(templates)
            prompt_texto = template.format(
                mood=mood_str,
                cores=cores_str,
                formato=random.choice(formatos) if formatos else "design"
            )
            
            # Adicionar variações
            variacoes = [
                "warm lighting", 
                "cool lighting", 
                "natural light",
                "soft shadows",
                "dramatic composition",
                "minimalist style"
            ]
            prompt_texto += f", {random.choice(variacoes)}, high quality, 4k"
            
            prompt_obj = {
                "prompt": prompt_texto,
                "formato": random.choice(["feed", "story", "banner"]),
                "seed": random.randint(0, 999999),
                "variacao": random.randint(1, 3),
                "descricao": f"Imagem {mood_str} - variação {i+1}",
                "processado": False,
                "aprovado": False
            }
            
            prompts.append(prompt_obj)
        
        return prompts
    
    def gerar(
        self, 
        style_guide: Dict[str, Any],
        num_prompts: int = 10,
        formato_base: str = "feed",
        usar_modelo_real: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Método principal de geração de prompts.
        
        Args:
            style_guide: O Style Guide extraído
            num_prompts: Número de prompts a gerar
            formato_base: Formato base das imagens
            usar_modelo_real: Usar modelo real (requer GPU) ou modo mock
            
        Returns:
            Lista de prompts em formato Dict
        """
        if usar_modelo_real:
            return self.gerar_com_ollama(style_guide, num_prompts)
        else:
            return self.gerar_mock(style_guide, num_prompts, formato_base)
    
    def salvar_prompts(self, prompts: List[Dict[str, Any]], caminho: Optional[Path] = None) -> Path:
        """Salva os prompts em arquivo JSON."""
        if caminho is None and self.pasta_projeto:
            caminho = self.pasta_projeto / "prompts.json"
        
        if caminho:
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, indent=2, ensure_ascii=False)
            return caminho
        
        raise ValueError("Caminho não especificado e pasta_projeto não definida")
    
    @staticmethod
    def carregar_prompts(caminho: Path) -> List[Dict[str, Any]]:
        """Carrega prompts de arquivo."""
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def calcular_similaridade(self, prompt1: str, prompt2: str) -> float:
        """
        Calcula similaridade simples entre dois prompts.
        Em produção, usar embeddings e similaridade de cosseno.
        """
        # Dividir em palavras
        palavras1 = set(prompt1.lower().split())
        palavras2 = set(prompt2.lower().split())
        
        if not palavras1 or not palavras2:
            return 0.0
        
        # Interseção
        interseccao = palavras1 & palavras2
        
        # Similaridade de Jaccard
        return len(interseccao) / len(palavras1 | palavras2)
    
    def verificar_cache(
        self, 
        style_guide: Dict[str, Any], 
        prompts_anteriores: List[Dict[str, Any]],
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Verifica prompts em cache baseados em similaridade de style guide.
        Retorna prompts que podem ser reutilizados.
        """
        if not prompts_anteriores:
            return []
        
        cache_aprovados = [p for p in prompts_anteriores if p.get("aprovado")]
        
        if not cache_aprovados:
            return []
        
        # Gerar representation simples do style guide
        guide_repr = f"{style_guide.get('mood', {}).get('palavras_chave', [])}"
        
        similares = []
        for p in cache_aprovados:
            # Usar descrição como base de comparação
            desc = p.get("descricao", "")
            similaridade = self.calcular_similaridade(guide_repr, desc)
            if similaridade >= threshold:
                similares.append(p)
        
        return similares