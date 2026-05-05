#!/usr/bin/env python3
"""
Interface Gradio Completa para ArtisanAI Studio
GUI amigável para geração de imagens com IA.
"""

import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Adicionar pasta src ao path
sys.path.insert(0, str(Path(__file__).parent))

# Gradio opcional
try:
    import gradio as gr
    import numpy as np
    from PIL import Image
    GRADIO_DISPONIVEL = True
except ImportError:
    GRADIO_DISPONIVEL = False
    print("⚠️ Gradio não disponível. Execute: pip install gradio numpy pillow")
    sys.exit(1)


# Importar módulos do projeto
try:
    from src import Orquestrador
    from src.metadados import GerenciadorMetadados, MetadadosOpcoes
    from src.analisador_site import AnalisadorSiteFactory
    MODULOS_DISPONIVEIS = True
except ImportError:
    MODULOS_DISPONIVEIS = False


class InterfaceGUI:
    """Interface Gradio completa"""
    
    def __init__(self):
        self.orquestrador = None
        self.projeto_atual = None
        self.geracao_em_andamento = False
        self.resultado_final = None
    
    def _iniciar_geracao(
        self,
        projeto: str,
        briefing: str,
        modo: str,
        num_imagens: int,
        metadados: bool,
        camera: str
    ) -> tuple:
        """Inicia geração em thread separada"""
        self.geracao_em_andamento = True
        self.projeto_atual = projeto
        self.resultado_final = None
        
        def gerar():
            try:
                # Criar orquestrador
                self.orquestrador = Orquestrador(projeto, modo=modo)
                
                # Executar pipeline
                resultado = self.orquestrador.executar_pipeline_completo(
                    briefing=briefing,
                    num_imagens=num_imagens
                )
                
                # Adicionar metadados se solicitado
                if metadados and MODULOS_DISPONIVEIS:
                    pasta = Path("projetos") / projeto / "aprovadas"
                    if pasta.exists():
                        gerenciador = GerenciadorMetadados()
                        for img in pasta.glob("*.png"):
                            gerenciador.limpar_metadados(str(img), modo_profissional=True)
                        for img in pasta.glob("*.jpg"):
                            gerenciador.limpar_metadados(str(img), modo_profissional=True)
                
                self.resultado_final = resultado
                
            except Exception as e:
                self.resultado_final = {"erro": str(e)}
            finally:
                self.geracao_em_andamento = False
        
        # Iniciar thread
        thread = threading.Thread(target=gerar)
        thread.start()
        
        return "🚀 Geração iniciada!", ""
    
    def verificar_progresso(self) -> dict:
        """Verifica progresso da geração"""
        if not self.orquestrador:
            return {
                "status": "Aguardando...",
                "progresso": 0,
                "imagens": []
            }
        
        # Carregar estado
        estado = self.orquestrador.gerenciador.carregar_estado()
        
        if self.geracao_em_andamento:
            # Imagens já geradas
            pasta_aprovadas = Path("projetos") / self.projeto_atual / "aprovadas"
            pasta_rejeitadas = Path("projetos") / self.projeto_atual / "rejeitadas"
            
            imagens = []
            if pasta_aprovadas.exists():
                for img in pasta_aprovadas.glob("*"):
                    if img.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                        imagens.append(str(img))
            if pasta_rejeitadas.exists():
                for img in pasta_rejeitadas.glob("*"):
                    if img.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                        imagens.append(str(img))
            
            return {
                "status": f"Gerando... ({len(imagens)} imagens)",
                "progresso": 50,
                "imagens": imagens,
                "etapa": self.orquestrador.etapa_atual
            }
        elif self.resultado_final:
            if "erro" in self.resultado_final:
                return {
                    "status": f"Erro: {self.resultado_final['erro']}",
                    "progresso": 100,
                    "imagens": []
                }
            
            # Imagens finais
            pasta_aprovadas = Path("projetos") / self.projeto_atual / "aprovadas"
            imagens = []
            if pasta_aprovadas.exists():
                for img in pasta_aprovadas.glob("*"):
                    if img.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                        imagens.append(str(img))
            
            stats = self.resultado_final.get("estatisticas", {})
            
            return {
                "status": f"✅ Completo! {stats.get('total_imagens_aprovadas', 0)} aprovadas",
                "progresso": 100,
                "imagens": imagens,
                "stats": stats
            }
        
        return {
            "status": "Aguardando...",
            "progresso": 0,
            "imagens": []
        }
    
    def _analisar_site(self, url: str) -> str:
        """Analisa site para extrair estilo"""
        if not MODULOS_DISPONIVEIS:
            return "Módulos não disponíveis"
        
        try:
            resultado = AnalisadorSiteFactory.analisar(url, tipo="site")
            if resultado.get("status") == "sucesso":
                cores = resultado.get("cores", [])
                fontes = resultado.get("fontes", [])
                estilo = resultado.get("estilos", {})
                
                return f"""
### ✅ Análise Concluída

**Cores detectadas**: {', '.join(cores[:5]) if cores else 'Não detectadas'}

**Fontes detectadas**: {', '.join(fontes) if fontes else 'Não detectadas'}

**Estilo**: {estilo.get('mood', 'desconhecido')}
"""
            return f"Erro: {resultado.get('mensagem', 'Desconhecido')}"
        except Exception as e:
            return f"Erro: {str(e)}"
    
    def _analisar_instagram(self, username: str) -> str:
        """Analisa Instagram"""
        if not MODULOS_DISPONIVEIS:
            return "Módulos não disponíveis"
        
        if username.startswith("@"):
            username = username[1:]
        
        try:
            resultado = AnalisadorSiteFactory.analisar(username, tipo="instagram")
            if resultado.get("status") == "analisado":
                return f"""
### ✅ Perfil @{username}analisado

**Estilo visual**: {resultado.get('estilo_visual', 'desconhecido')}
**Tipos de conteúdo**: {', '.join(resultado.get('tipos_conteudo', []))}
**Consistência**: {resultado.get('consistency_score', 0):.1%}
"""
            return f"Erro: {resultado.get('mensagem', 'Desconhecido')}"
        except Exception as e:
            return f"Erro: {str(e)}"
    
    def criar(self) -> Any:
        """Cria interface completa"""
        
        with gr.Blocks(
            title="ArtisanAI Studio",
            theme=gr.themes.Soft(),
            css="""
            .main-title {text-align: center; font-size: 24px;}
            .status-box {padding: 20px; background: #f0f0f0; border-radius: 10px;}
            """
        ) as app:
            
            gr.Markdown("""
            # 🏭 ArtisanAI Studio
            ### Fábrica Autônoma de Design com IA
            
            Gere imagens profissionais a partir de descrições textuais.
            """)
            
            with gr.Tab("🎨 Gerar Imagens"):
                with gr.Row():
                    with gr.Column(scale=1):
                        projeto = gr.Textbox(
                            label="Nome do Projeto",
                            placeholder="meu_projeto",
                            value="projeto"
                        )
                        
                        briefing = gr.Textbox(
                            label="Briefing / Descrição",
                            placeholder="Ex: Fashion elegante, minimal, sophistication...",
                            lines=3
                        )
                    
                    with gr.Column(scale=1):
                        modo = gr.Radio(
                            choices=[("Básico (rápido)", "basic"), 
                                    ("Profissional (rev manual)", "pro"),
                                    ("Portfólio (rigoroso)", "portfolio")],
                            label="Modo de Operação",
                            value="basic"
                        )
                        
                        num_imagens = gr.Slider(
                            minimum=1, maximum=20, value=5, step=1,
                            label="Número de Imagens"
                        )
                
                with gr.Row():
                    with gr.Column(scale=1):
                        metadados = gr.Checkbox(
                            label="Adicionar metadados falsos (câmera profissional)",
                            value=False
                        )
                        
                        camera = gr.Dropdown(
                            choices=["canon_eos", "nikon_d850", "sony_a7r"],
                            label="Câmera (para metadados)",
                            value="canon_eos"
                        )
                    
                    with gr.Column(scale=1):
                        gerar_btn = gr.Button("🚀 Gerar Imagens", variant="primary")
                        limpar_btn = gr.Button("🗑️ Limpar Projeto")
                
                # Status
                status_output = gr.Markdown(value="")
                progresso = gr.Slider(value=0, maximum=100, label="Progresso")
                
                # Galería de imagens
                galeria = gr.Gallery(
                    label="Imagens Geradas",
                    columns=4,
                    rows=4
                )
                
                # Ações após geração
                with gr.Row():
                    baixar_btn = gr.Button("📥 Baixar Projeto (ZIP)")
                    relatorio_btn = gr.Button("📊 Ver Relatório")
                
                # Event handlers
                def on_gerar(p, b, m, n, md, c):
                    gui = InterfaceGUI()
                    status, _ = gui._iniciar_geracao(p, b, m, n, md, c)
                    return status, 50
                
                def on_limpar(p):
                    import shutil
                    pasta = Path("projetos") / p
                    if pasta.exists():
                        shutil.rmtree(pasta)
                    return "✅ Projeto limpo!", [], 0
                
                gerar_btn.click(
                    on_gerar,
                    inputs=[projeto, briefing, modo, num_imagens, metadados, camera],
                    outputs=[status_output, progresso]
                )
                
                # Atualizar galeria periodicamente
                def atualizar_galeria():
                    gui = InterfaceGUI()
                    if gui.projeto_atual:
                        estado = gui.verificar_progresso()
                        return estado.get("imagens", []), estado.get("progresso", 0)
                    return [], 0
                
                galeria.change(
                    atualizar_galeria,
                    outputs=[galeria, progresso]
                )
            
            with gr.Tab("🌐 Análise de Site"):
                gr.Markdown("### Extraia estilo de websites")
                
                with gr.Row():
                    with gr.Column():
                        url_input = gr.Textbox(
                            label="URL do Site",
                            placeholder="https://exemplo.com"
                        )
                        analisar_site_btn = gr.Button("🔍 Analisar Site")
                    
                    with gr.Column():
                        resultado_site = gr.Markdown(value="")
                
                gr.Markdown("---")
                gr.Markdown("### Análise de Instagram")
                
                with gr.Row():
                    with gr.Column():
                        instagram_input = gr.Textbox(
                            label="Usuário Instagram",
                            placeholder="@empresa"
                        )
                        analisar_ig_btn = gr.Button("📸 Analisar Instagram")
                    
                    with gr.Column():
                        resultado_ig = gr.Markdown(value="")
                
                def on_analisar_site(url):
                    gui = InterfaceGUI()
                    return gui._analisar_site(url)
                
                def on_analisar_instagram(username):
                    gui = InterfaceGUI()
                    return gui._analisar_instagram(username)
                
                analisar_site_btn.click(
                    on_analisar_site,
                    inputs=[url_input],
                    outputs=[resultado_site]
                )
                
                analisar_ig_btn.click(
                    on_analisar_instagram,
                    inputs=[instagram_input],
                    outputs=[resultado_ig]
                )
            
            with gr.Tab("📁 Projetos"):
                gr.Markdown("### Projetos Salvos")
                
                projetos = gr.Dropdown(
                    choices=self._listar_projetos(),
                    label="Selecionar Projeto"
                )
                
                with gr.Row():
                    ver_btn = gr.Button("👁️ Ver Projeto")
                    excluir_btn = gr.Button("🗑️ Excluir")
                
                projeto_galeria = gr.Gallery(label="Imagens do Projeto")
                projeto_info = gr.JSON(label="Informações")
                
                def on_ver_projeto(projeto):
                    pasta = Path("projetos") / projeto
                    imagens = []
                    if pasta.exists():
                        pasta_img = pasta / "aprovadas"
                        if pasta_img.exists():
                            for img in pasta_img.glob("*"):
                                if img.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                                    imagens.append(str(img))
                    
                    info = {}
                    style_guide = pasta / "style_guide.json"
                    if style_guide.exists():
                        import json
                        with open(style_guide) as f:
                            info = json.load(f)
                    
                    return imagens, info
                
                def on_excluir(projeto):
                    import shutil
                    pasta = Path("projetos") / projeto
                    if pasta.exists():
                        shutil.rmtree(pasta)
                    return [], {}, self._listar_projetos()
                
                ver_btn.click(
                    on_ver_projeto,
                    inputs=[projetos],
                    outputs=[projeto_galeria, projeto_info]
                )
                
                excluir_btn.click(
                    on_excluir,
                    inputs=[projetos],
                    outputs=[projeto_galeria, projeto_info, projetos]
                )
            
            with gr.Tab("❓ Ajuda"):
                gr.Markdown("""
                ## ℹ️ Como Usar
                
                ### 1. Gerar Imagens
                1. Dê um nome ao projeto
                2. Descreva o que deseja (briefing)
                3. Escolha o modo:
                   - **Básico**: Rápido, avaliação automática
                   - **Profissional**: Revisão manual
                   - **Portfólio**: Avaliação rigorosa
                4. Clique em "Gerar Imagens"
                
                ### 2. Metadados
                Marque "Adicionar metadados falsos" para:
                - Remover rastros de IA
                - Adicionar dados de câmera profissional
                - Tornar imagens mais realistas
                
                ### 3. Análise de Site
                Use a aba "Análise de Site" para:
                - Extrair paleta de cores
                - Detectar fontes
                - Analisar consistência do Instagram
                
                ## Requisitos
                - Python 3.9+
                - GPU recomendada (T4 ou superior)
                - 10GB+ Disco
                """)
        
        return app
    
    def _listar_projetos(self) -> List[str]:
        """Lista projetos existentes"""
        pasta = Path("projetos")
        if not pasta.exists():
            return []
        
        projetos = []
        for d in pasta.iterdir():
            if d.is_dir():
                projetos.append(d.name)
        
        return sorted(projetos)


def iniciar_interface():
    """Inicia a interface Gradio"""
    if not GRADIO_DISPONIVEL:
        print("❌ Gradio não disponível")
        print("Execute: pip install gradio")
        return
    
    print("🚀 Iniciando ArtisanAI Studio...")
    print("📊 Acesse: http://localhost:7860")
    
    gui = InterfaceGUI()
    app = gui.criar()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    iniciar_interface()