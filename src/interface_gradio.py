#!/usr/bin/env python3
"""
Interface Gradio para Revisão Manual (Modo Profissional)
Permite ao usuário aprovar/rejeitar/variar imagens geradas.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# gradio é opcional (usado apenas no modo profissional)
try:
    import gradio as gr
    GRADIO_DISPONIVEL = True
except ImportError:
    GRADIO_DISPONIVEL = False


class InterfaceGradio:
    """Interface Gradio para revisão manual de imagens."""
    
    def __init__(self, pasta_projeto: Optional[Path] = None):
        self.pasta_projeto = pasta_projeto
        self.imagens_pendentes = []
        self.imagens_aprovadas = []
        self.imagens_rejeitadas = []
        self.indice_atual = 0
    
    def _criar_interface(self) -> Any:
        """Cria a interface Gradio."""
        if not GRADIO_DISPONIVEL:
            raise ImportError("Gradio não está instalado. Execute: pip install gradio")
        
        with gr.Blocks(title="ArtisanAI Studio - Revisão Manual") as demo:
            gr.Markdown("# 🎨 ArtisanAI Studio - Revisão Manual")
            gr.Markdown("Selecione as imagens que deseja aprovar.")
            
            with gr.Row():
                with gr.Column():
                    self.output_imagem = gr.Gallery(
                        label="Imagens Geradas",
                        columns=2,
                        rows=2
                    )
                
                with gr.Column():
                    self.info_prompt = gr.Textbox(
                        label="Prompt",
                        interactive=False,
                        lines=3
                    )
            
            with gr.Row():
                self.btn_aprovar = gr.Button("✅ Aprovar", variant="primary")
                self.btn_rejeitar = gr.Button("❌ Rejeitar", variant="secondary")
                self.btn_variar = gr.Button("🔄 Regenerar", variant="secondary")
            
            gr.Markdown("### Estatísticas")
            with gr.Row():
                self.estat_aprovadas = gr.Number(label="Aprovadas", value=0)
                self.estat_rejeitadas = gr.Number(label="Rejeitadas", value=0)
            
            # Event handlers
            self.btn_aprovar.click(
                self._aprovar,
                inputs=[self.output_imagem],
                outputs=[self.estat_aprovadas]
            )
            self.btn_rejeitar.click(
                self._rejeitar,
                inputs=[self.output_imagem],
                outputs=[self.estat_rejeitadas]
            )
        
        return demo
    
    def _aprovar(self, galeria: List) -> Tuple[int, Dict]:
        """Marca imagens como aprovadas."""
        imagens_selecionadas = [img for img in galeria if img.get("selected")]
        
        for img in imagens_selecionadas:
            caminho = img.get("path")
            if caminho:
                self.imagens_aprovadas.append(caminho)
        
        self.indice_atual += 1
        return len(self.imagens_aprovadas), {"value": self._proxima_imagem()}
    
    def _rejeitar(self, galeria: List) -> Tuple[int, Dict]:
        """Marca imagens como rejeitadas."""
        imagens_selecionadas = [img for img in galeria if img.get("selected")]
        
        for img in imagens_selecionadas:
            caminho = img.get("path")
            if caminho:
                self.imagens_rejeitadas.append({
                    "caminho": caminho,
                    "motivo": "rejeitado_manual"
                })
        
        self.indice_atual += 1
        return len(self.imagens_rejeitadas), {"value": self._proxima_imagem()}
    
    def _variar(self, galeria: List) -> Tuple[Dict, Any]:
        """Regenera imagens com mismo prompt."""
        # Retorna para o designer regenerar
        return {"acao": "variar", "indice": self.indice_atual}
    
    def _proxima_imagem(self) -> Dict:
        """Retorna a próxima imagem para revisão."""
        if self.indice_atual < len(self.imagens_pendentes):
            return self.imagens_pendentes[self.indice_atual]
        return None
    
    def carregar_imagens(self, caminhos: List[str]) -> None:
        """Carrega imagens para revisão."""
        self.imagens_pendentes = caminhos
        self.indice_atual = 0
    
    def iniciar(self) -> None:
        """Inicia a interface Gradio."""
        if not GRADIO_DISPONIVEL:
            print("⚠️ Gradio não disponível. Install: pip install gradio")
            return
        
        Interface = self._criar_interface()
        Interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=True
        )
    
    def get_estatisticas(self) -> Dict[str, int]:
        """Retorna estatísticas da sessão."""
        return {
            "total_pendentes": len(self.imagens_pendentes),
            "aprovadas": len(self.imagens_aprovadas),
            "rejeitadas": len(self.imagens_rejeitadas)
        }
    
    def mover_para_pasta(self, caminho: Path, pasta_destino: Path) -> Path:
        """Move imagem para pasta de destino."""
        pasta_destino.mkdir(parents=True, exist_ok=True)
        
        nome = caminho.name
        destino = pasta_destino / nome
        
        import shutil
        shutil.move(str(caminho), str(destino))
        
        return destino
    
    def salvar_historico(self, caminho: Path) -> None:
        """Salva histórico de decisões."""
        import json
        
        historico = {
            "aprovadas": self.imagens_aprovadas,
            "rejeitadas": self.imagens_rejeitadas,
            "estatisticas": self.get_estatisticas()
        }
        
        with open(caminho, 'w') as f:
            json.dump(historico, f, indent=2)
    
    def carregar_historico(self, caminho: Path) -> None:
        """Carrega histórico de decisões."""
        import json
        
        if caminho.exists():
            with open(caminho, 'r') as f:
                historico = json.load(f)
            
            self.imagens_aprovadas = historico.get("aprovadas", [])
            self.imagens_rejeitadas = historico.get("rejeitadas", [])