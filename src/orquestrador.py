#!/usr/bin/env python3
"""
Orquestrador do Pipeline
Coordena a execução sequencial dos agentes e gerencia o fluxo de trabalho.
"""

import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Importar módulos locais
from .gerenciador_estado import GerenciadorEstado
from .agente_analisador import AgenteAnalisador
from .agente_prompter import AgentePrompter
from .agente_designer import AgenteDesigner
from .agente_juiz import AgenteJuiz


class Orquestrador:
    """Orquestra o pipeline completo de geração de imagens."""
    
    # Etapas do pipeline
    ETAPAS = [
        "inicializado",
        "style_guide_gerado",
        "prompts_gerados", 
        "imagens_gerando",
        "imagens_avaliando",
        "completo"
    ]
    
    def __init__(self, nome_projeto: str, pasta_projetos: str = "projetos", modo: str = "basic"):
        self.nome_projeto = nome_projeto
        self.pasta_projetos = Path(pasta_projetos)
        self.modo = modo
        
        # Inicializar gerenciador de estado
        self.gerenciador = GerenciadorEstado(nome_projeto, pasta_projetos)
        
        # Inicializar agentes com modo
        self.analisador = AgenteAnalisador(self.gerenciador.pasta_projeto)
        self.prompter = AgentePrompter(self.gerenciador.pasta_projeto)
        self.designer = AgenteDesigner(self.gerenciador.pasta_projeto, modo=modo)
        self.juiz = AgenteJuiz(modo=modo)
        
        # Estado atual
        self.etapa_atual = "inicializado"
        self.progresso = 0.0
    
    def inicializar_projeto(
        self, 
        briefing: str, 
        imagens_referencia: Optional[List[str]] = None,
        num_imagens: int = 10
    ) -> Dict[str, Any]:
        """Inicializa um novo projeto."""
        # Verificar se já existe estado
        if self.gerenciador.verificar_estado_existente():
            estado_existente = self.gerenciador.carregar_estado()
            if estado_existente:
                print(f"Projeto '{self.nome_projeto}' já existe.")
                return {
                    "status": "existente",
                    "estado": estado_existente,
                    "mensagem": "Deseja retomar ou iniciar novo projeto?"
                }
        
        # Inicializar estado
        estado = self.gerenciador.inicializar_estado(briefing, imagens_referencia)
        estado["configuracao"]["num_imagens_desejadas"] = num_imagens
        
        print(f"Projeto '{self.nome_projeto}' inicializado.")
        print(f"Briefing: {briefing[:100]}...")
        
        return {
            "status": "sucesso",
            "estado": estado
        }
    
    def verificar_retomada(self) -> Optional[Dict[str, Any]]:
        """Verifica se há um projeto existente para retomar."""
        if self.gerenciador.verificar_estado_existente():
            estado = self.gerenciador.carregar_estado()
            if estado:
                self.etapa_atual = estado.get("etapa_atual", "inicializado")
                return estado
        return None
    
    def executar_etapa_analise(
        self, 
        briefing: str,
        imagens_referencia: Optional[List[str]] = None,
        usar_modelo_real: bool = False
    ) -> Dict[str, Any]:
        """Executa a etapa de análise de estilo."""
        print("=" * 50)
        print("ETAPA 1: ANALISADOR DE ESTILO")
        print("=" * 50)
        
        # Verificar se já existe style guide
        style_guide = self.gerenciador.carregar_style_guide()
        if style_guide:
            print("Style Guide já existe. Usando existente.")
            return {
                "status": "sucesso",
                "style_guide": style_guide,
                "acao": "usar_existente"
            }
        
        # Executar análise
        style_guide = self.analisador.analisar(
            briefing=briefing,
            imagens_paths=imagens_referencia,
            usar_modelo_real=usar_modelo_real
        )
        
        # Salvar style guide
        self.gerenciador.salvar_style_guide(style_guide)
        self.etapa_atual = "style_guide_gerado"
        
        print(f"Style Guide salvo em: {self.gerenciador.pasta_projeto / 'style_guide.json'}")
        print(f"Paleta de cores: {style_guide.get('paleta_cores', {}).get('principais', [])[:3]}")
        
        return {
            "status": "sucesso",
            "style_guide": style_guide,
            "modelo_usado": self.analisador.modelo_selecionado
        }
    
    def executar_etapa_prompts(
        self, 
        style_guide: Optional[Dict[str, Any]] = None,
        num_prompts: Optional[int] = None,
        usar_modelo_real: bool = False
    ) -> Dict[str, Any]:
        """Executa a etapa de geração de prompts."""
        print("=" * 50)
        print("ETAPA 2: AGENTE PROMPTER")
        print("=" * 50)
        
        # Carregar style guide se não fornecido
        if style_guide is None:
            style_guide = self.gerenciador.carregar_style_guide()
        
        if not style_guide:
            return {
                "status": "erro",
                "mensagem": "Style Guide não encontrado. Execute a etapa de análise primeiro."
            }
        
        # Verificar se já existem prompts
        prompts_existente = self.gerenciador.carregar_prompts()
        if prompts_existente:
            print(f"Já existem {len(prompts_existente)} prompts salvos.")
            return {
                "status": "sucesso",
                "prompts": prompts_existente,
                "acao": "usar_existente"
            }
        
        # Determinar número de prompts (N * 1.5 com margem de segurança)
        if num_prompts is None:
            estado = self.gerenciador.carregar_estado()
            num_desejados = estado.get("configuracao", {}).get("num_imagens_desejadas", 10)
            num_prompts = int(num_desejados * 1.5)
        
        # Gerar prompts
        prompts = self.prompter.gerar(
            style_guide=style_guide,
            num_prompts=num_prompts,
            usar_modelo_real=usar_modelo_real
        )
        
        # Salvar prompts
        self.gerenciador.salvar_prompts(prompts)
        self.etapa_atual = "prompts_gerados"
        
        print(f"Gerados {len(prompts)} prompts")
        
        return {
            "status": "sucesso",
            "prompts": prompts,
            "modelo_usado": self.prompter.modelo_selecionado
        }
    
    def executar_etapa_geracao(
        self, 
        prompts: Optional[List[Dict[str, Any]]] = None,
        max_tentativas: int = 3
    ) -> Dict[str, Any]:
        """Executa a etapa de geração de imagens."""
        print("=" * 50)
        print("ETAPA 3: DESIGNER (GERAÇÃO DE IMAGENS)")
        print("=" * 50)
        
        # Carregar prompts se não fornecidos
        if prompts is None:
            # Buscar prompts não processados
            prompt_atual = self.gerenciador.get_proximo_prompt()
            if prompt_atual:
                prompts = [prompt_atual]
        
        if not prompts:
            return {
                "status": "erro",
                "mensagem": "Nenhum prompt encontrado."
            }
        
        # Atualizar etapa
        self.etapa_atual = "imagens_gerando"
        
        # Processar cada prompt
        resultados = []
        for i, dados_prompt in enumerate(prompts):
            prompt = dados_prompt.get("prompt", "")
            formato = dados_prompt.get("formato", "feed")
            seed = dados_prompt.get("seed")
            
            print(f"\nGerando imagem {i+1}/{len(prompts)}...")
            print(f"Prompt: {prompt[:80]}...")
            
            # Tentar gerar imagem
            for tentativa in range(max_tentativas):
                try:
                    caminho, seed_usado = self._gerar_imagem(
                        prompt=prompt,
                        formato=formato,
                        seed=seed
                    )
                    
                    # Registrar imagem gerada
                    self.gerenciador.registrar_imagem_gerada(str(caminho), prompt)
                    
                    resultados.append({
                        "indice": i,
                        "caminho": str(caminho),
                        "seed": seed_usado,
                        "prompt": prompt,
                        "sucesso": True,
                        "tentativa": tentativa + 1
                    })
                    break
                    
                except Exception as e:
                    print(f"Tentativa {tentativa+1} falhou: {e}")
                    if tentativa == max_tentativas - 1:
                        resultados.append({
                            "indice": i,
                            "prompt": prompt,
                            "sucesso": False,
                            "erro": str(e)
                        })
        
        print(f"\n{len([r for r in resultados if r.get('sucesso')])}/{len(resultados)} imagens geradas com sucesso.")
        
        return {
            "status": "sucesso",
            "resultados": resultados
        }
    
    def _gerar_imagem(self, prompt: str, formato: str, seed: Optional[int] = None) -> Tuple[Path, int]:
        """Método interno para gerar uma imagem."""
        caminho, seed_usado = self.designer.gerar_imagem(
            prompt=prompt,
            formato=formato,
            seed=seed
        )
        return caminho, seed_usado
    
    def executar_etapa_avaliacao(
        self, 
        num_imagens_desejadas: Optional[int] = None
    ) -> Dict[str, Any]:
        """Executa a etapa de avaliação de imagens."""
        print("=" * 50)
        print("ETAPA 4: JUIZ (AVALIAÇÃO)")
        print("=" * 50)
        
        # Carregar estado
        estado = self.gerenciador.carregar_estado()
        if not estado:
            return {"status": "erro", "mensagem": "Estado não encontrado"}
        
        # Obter imagens pendentes
        imagens_pendentes = [
            img for img in estado.get("imagens_geradas", [])
            if img.get("status") == "pendente"
        ]
        
        if not imagens_pendentes:
            return {
                "status": "aviso",
                "mensagem": "Nenhuma imagem pendente para avaliar"
            }
        
        # Determinar limite
        if num_imagens_desejadas is None:
            num_imagens_desejadas = estado.get("configuracao", {}).get(
                "num_imagens_desejadas", 10
            )
        
        count_aprovadas = 0
        count_rejeitadas = 0
        resultados = []
        
        self.etapa_atual = "imagens_avaliando"
        
        for img in imagens_pendentes:
            # Verificar se já atingiu o目标
            if count_aprovadas >= num_imagens_desejadas:
                break
            
            caminho = img.get("caminho", "")
            prompt = img.get("prompt", "")
            
            if not caminho or not prompt:
                continue
            
            print(f"\nAvaliando: {caminho}")
            
            # Avaliar imagem
            avaliacao = self.juiz.avaliar_imagem(caminho, prompt)
            
            if avaliacao.get("aprovado"):
                count_aprovadas += 1
                self.gerenciador.registrar_imagem_aprovada(
                    caminho, prompt, avaliacao
                )
                print(f"✓ Aprovada! CLIP: {avaliacao.get('clip', 0):.2f}, "
                      f"Aesthetic: {avaliacao.get('aesthetic', 0):.1f}")
            else:
                count_rejeitadas += 1
                self.gerenciador.registrar_imagem_rejeitada(
                    caminho, prompt, 
                    f"CLIP: {avaliacao.get('clip', 0):.2f}, "
                    f"Aesthetic: {avaliacao.get('aesthetic', 0):.1f}"
                )
                print(f"✗ Rejeitada")
            
            resultados.append({
                "caminho": caminho,
                "prompt": prompt,
                **avaliacao
            })
        
        print(f"\n{count_aprovadas} imagens aprovadas, {count_rejeitadas} rejeitadas")
        
        # Atualizar etapa se atingiu o目标
        if count_aprovadas >= num_imagens_desejadas:
            self.etapa_atual = "completo"
        
        # Obter estatísticas finais
        estatisticas = self.gerenciador.get_estatisticas()
        
        return {
            "status": "sucesso",
            "aprovadas": count_aprovadas,
            "rejeitadas": count_rejeitadas,
            "resultados": resultados,
            "estatisticas": estatisticas
        }
    
    def executar_pipeline_completo(
        self,
        briefing: str,
        imagens_referencia: Optional[List[str]] = None,
        num_imagens: int = 10,
        usar_modelo_real: bool = False,
        revisar_humano: bool = False
    ) -> Dict[str, Any]:
        """Executa o pipeline completo de uma vez."""
        resultados = {
            "projeto": self.nome_projeto,
            "iniciado_em": datetime.now().isoformat(),
            "etapas": {}
        }
        
        # Etapa 1: Inicializar
        init_result = self.inicializar_projeto(briefing, imagens_referencia, num_imagens)
        resultados["etapas"]["inicializacao"] = init_result
        
        # Etapa 2: Análise
        analise_result = self.executar_etapa_analise(briefing, imagens_referencia, usar_modelo_real)
        resultados["etapas"]["analise"] = analise_result
        
        # Etapa 3: Prompts
        prompts_result = self.executar_etapa_prompts(
            analise_result.get("style_guide"),
            num_imagens,
            usar_modelo_real
        )
        resultados["etapas"]["prompts"] = prompts_result
        
        # Etapa 4: Geração e Avaliação em loop
        imagens_geradas = []
        imagens_aprovadas = 0
        tentativas = 0
        max_tentativas_total = num_imagens * 3
        
        estado = self.gerenciador.carregar_estado()
        prompts_list = estado.get("prompts", []) if estado else []
        
        # Carregar prompts não processados
        prompts_nao_processados = [
            p for p in prompts_list 
            if not p.get("processado")
        ]
        
        while imagens_aprovadas < num_imagens and tentativas < max_tentativas_total:
            if not prompts_nao_processados:
                # Gerar mais prompts se necessário
                prompts_extra = self.executar_etapa_prompts(
                    analise_result.get("style_guide"),
                    num_imagens,
                    usar_modelo_real
                )
                prompts_list = estado.get("prompts", []) if estado else []
                prompts_nao_processados = [
                    p for p in prompts_list 
                    if not p.get("processado")
                ]
            
            if not prompts_nao_processados:
                break
            
            # Pegar próximo prompt
            prompt_dados = prompts_nao_processados.pop(0)
            
            # Gerar imagem
            geracao_result = self.executar_etapa_geracao([prompt_dados])
            imagens_geradas.extend(geracao_result.get("resultados", []))
            
            # Avaliar última imagem gerada
            if geracao_result.get("resultados"):
                ultimo = geracao_result["resultados"][-1]
                if ultimo.get("sucesso"):
                    avaliacao = self.juiz.avaliar_imagem(
                        ultimo.get("caminho", ""),
                        prompt_dados.get("prompt", "")
                    )
                    
                    if avaliacao.get("aprovado"):
                        imagens_aprovadas += 1
                        self.gerenciador.registrar_imagem_aprovada(
                            ultimo.get("caminho", ""),
                            prompt_dados.get("prompt", ""),
                            avaliacao
                        )
                        self.gerenciador.marcar_prompt_aprovado(prompt_dados.get("prompt", ""))
                    else:
                        self.gerenciador.registrar_imagem_rejeitada(
                            ultimo.get("caminho", ""),
                            prompt_dados.get("prompt", ""),
                            "Reprovada pelo Juiz"
                        )
                    
                    # Marcar prompt como processado
                    self.gerenciador.marcar_prompt_processado(prompt_dados.get("prompt", ""))
            
            tentativas += 1
        
        # Estatísticas finais
        resultados["finalizado_em"] = datetime.now().isoformat()
        resultados["estatisticas"] = self.gerenciador.get_estatisticas()
        
        return resultados
    
    def gerar_relatorio(self) -> str:
        """Gera um relatório em Markdown do projeto."""
        estado = self.gerenciador.carregar_estado()
        if not estado:
            return "# Projeto não encontrado"
        
        # Obter style guide
        style_guide = self.gerenciador.carregar_style_guide()
        
        # Construir relatório
        relatorio = f"""# ArtisanAI Studio - Relatório do Projeto

## {self.nome_projeto}

**Criado em**: {estado.get('criado_em', 'N/A')}
**Última atualização**: {estado.get('atualizado_em', 'N/A')}
**Etapa atual**: {estado.get('etapa_atual', 'N/A')}

---

## Briefing

{estado.get('briefing', 'N/A')}

---

## Style Guide

### Paleta de Cores
- **Principais**: {style_guide.get('paleta_cores', {}).get('principais', []) if style_guide else []}
- **Secundárias**: {style_guide.get('paleta_cores', {}).get('secundarias', []) if style_guide else []}
- **Acentos**: {style_guide.get('paleta_cores', {}).get('acentos', []) if style_guide else []}

### Mood
- **Palavras-chave**: {style_guide.get('mood', {}).get('palavras_chave', []) if style_guide else []}
- **Emoções**: {style_guide.get('mood', {}).get('emoções', []) if style_guide else []}

### Tipografia
- **Fontes**: {style_guide.get('tipografia', {}).get('familias', []) if style_guide else []}

---

## Resultados

- **Imagens geradas**: {len(estado.get('imagens_geradas', []))}
- **Imagens aprovadas**: {len(estado.get('imagens_aprovadas', []))}
- **Imagens rejeitadas**: {len(estado.get('imagens_rejeitadas', []))}

---

## Métricas Médias

"""

        # Calculate average correctly
        clip_scores = estado.get('metricas', {}).get('clip_score', [])
        aesthetic_scores = estado.get('metricas', {}).get('aesthetic_score', [])
        brisque_scores = estado.get('metricas', {}).get('brisque_score', [])

        avg_clip = sum(clip_scores) / len(clip_scores) if clip_scores else 0
        avg_aesthetic = sum(aesthetic_scores) / len(aesthetic_scores) if aesthetic_scores else 0
        avg_brisque = sum(brisque_scores) / len(brisque_scores) if brisque_scores else 0

        relatorio += f"""- **CLIP Score**: {avg_clip:.2f}
- **Aesthetic Score**: {avg_aesthetic:.1f}
- **BRISQUE Score**: {avg_brisque:.1f}

---

*Relatório gerado automaticamente pelo ArtisanAI Studio*
"""
        
        return relatorio
    
    def get_progresso(self) -> float:
        """Retorna o progresso atual do pipeline (0-1)."""
        estado = self.gerenciador.carregar_estado()
        if not estado:
            return 0.0
        
        total = estado.get("configuracao", {}).get("num_imagens_desejadas", 10)
        aprovadas = len(estado.get("imagens_aprovadas", []))
        
        return min(aprovadas / total, 1.0)