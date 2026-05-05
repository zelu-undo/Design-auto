#!/usr/bin/env python3
"""
ArtisanAI Studio - Ponto de Entrada

Uso simples:
    python main.py -p meu_projeto -b "Fashion moderna"
    
Modos de operação:
    --modo basic      (padrão)    SDXL-Turbo, avaliação automática
    --modo pro                   Flux.1 Schnell, revisão manual via Gradio
    --modo portfolio             Flux.1 Schnell, avaliação rigorosa automática
    
Opções de metadados:
    --metadados                 Adicionar metadados falsos de câmera profissional
    --camera canon_eos|nikon_d850|sony_a7r  Tipo de câmera
    
Análise de site:
    --analisar-site URL        Analisar website para extrair estilo
    --analisar-instagram @user  Analisar perfil do Instagram
"""

import argparse
import sys
from pathlib import Path

# Adicionar pasta atual ao path
sys.path.insert(0, str(Path(__file__).parent))

# Importar módulos
try:
    from src import Orquestrador
    from src.metadados import GerenciadorMetadados, MetadadosOpcoes
    from src.analisador_site import AnalisadorSiteFactory
except ImportError as e:
    print(f"Erro ao importar: {e}")
    sys.exit(1)


def modo_analise_site(args):
    """Executa modo de análise de site."""
    print(f"🌐 Analisando site: {args.analisar_site}")
    print("=" * 50)
    
    resultado = AnalisadorSiteFactory.analisar(args.analisar_site, tipo="site")
    
    if resultado.get("status") == "sucesso":
        print("✅ Análise concluída!")
        print(f"\n📊 Cores detectadas: {resultado.get('cores', [])}")
        print(f"🔤 Fontes detectadas: {resultado.get('fontes', [])}")
        print(f"🎨 Estilo: {resultado.get('estilos', {})}")
        print(f"🖼️  Total de imagens: {resultado.get('total_imagens', 0)}")
        
        # Oferecer para usar como base
        if resultado.get("cores"):
            usar = input("\nUsar estas cores como base do projeto? (s/n): ").lower()
            if usar == "s":
                from src.agente_analisador import AgenteAnalisador
                analisador = AgenteAnalisador()
                
                style_guide = {
                    "paleta_cores": {
                        "principais": resultado.get("cores", [])[:3],
                        "descricao": f"Cores extraídas do site {args.analisar_site}"
                    },
                    "tipografia": {
                        "familias": resultado.get("fontes", []),
                        "descricao": f"Fontes extraídas do site"
                    },
                    "mood": resultado.get("estilos", {})
                }
                
                # Salvar
                pasta = Path("projetos") / args.projeto
                pasta.mkdir(parents=True, exist_ok=True)
                
                import json
                with open(pasta / "style_guide.json", "w") as f:
                    json.dump(style_guide, f, indent=2)
                
                print(f"✅ Style Guide salvo em: {pasta / 'style_guide.json'}")
    else:
        print(f"❌ Erro: {resultado.get('mensagem', 'Desconhecido')}")


def modo_analise_instagram(args):
    """Executa modo de análise de Instagram."""
    username = args.analisar_instagram.replace("@", "").strip()
    print(f"📸 Analisando Instagram: @{username}")
    print("=" * 50)
    
    resultado = AnalisadorSiteFactory.analisar(username, tipo="instagram")
    
    if resultado.get("status") == "analisado":
        print("✅ Análise concluída!")
        print(f"\n🔤 Estilo visual: {resultado.get('estilo_visual')}")
        print(f"📊 Consistência: {resultado.get('consistency_score', 0):.1%}")
        print(f"📝 Tipos de conteúdo: {resultado.get('tipos_conteudo')}")
        
        # Oferecer para usar como base
        if resultado.get("cores_principais"):
            usar = input("\nUsar paleta como base do projeto? (s/n): ").lower()
            if usar == "s":
                import json
                pasta = Path("projetos") / args.projeto
                pasta.mkdir(parents=True, exist_ok=True)
                
                style_guide = {
                    "paleta_cores": {
                        "principais": resultado.get("cores_principais", []),
                        "descricao": f"Paleta extraída do Instagram @{username}"
                    },
                    "mood": {"estilo": resultado.get("estilo_visual")},
                    "fontes": resultado.get("paletas_detectadas", [])
                }
                
                with open(pasta / "style_guide.json", "w") as f:
                    json.dump(style_guide, f, indent=2)
                
                print(f"✅ Style Guide salvo!")
    else:
        print(f"❌ Erro: {resultado.get('mensagem', 'Desconhecido')}")


def adicionar_metadados(args):
    """Adiciona metadados às imagens geradas."""
    if not args.metadados:
        return
    
    print("🏷️  Adicionando metadados às imagens...")
    
    pasta_imagens = Path("projetos") / args.projeto / "aprovadas"
    if not pasta_imagens.exists():
        print(f"⚠️ Pasta não encontrada: {pasta_imagens}")
        return
    
    # Obter configurações de câmera
    opcoes = MetadadosOpcoes.get_opcoes()
    cameras = opcoes.get("cameras", {})
    
    camera_config = cameras.get(args.camera, cameras.get("canon_eos"))
    
    gerenciador = GerenciadorMetadados()
    
    # Processar todas as imagens
    imagens = list(pasta_imagens.glob("*.png")) + list(pasta_imagens.glob("*.jpg"))
    
    print(f"📷 Encontradas {len(imagens)} imagens")
    
    for img in imagens:
        sucesso, msg = gerenciador.limpar_metadados(
            str(img),
            modo_profissional=True,
            usar_lente=True,
            usar_local=False
        )
        if sucesso:
            print(f"✅ {img.name}: {msg}")
        else:
            print(f"❌ {img.name}: {msg}")
    
    print("🏷️  Metadados adicionados!")


def main():
    parser = argparse.ArgumentParser(
        description="🏭 ArtisanAI Studio - Fábrica de Design Autônoma",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # Modo Básico (padrão)
  python main.py -p meu_projeto -b "Fashion moderna"
  
  # Modo Profissional
  python main.py -p meu_projeto -b "Logo startup" --modo pro
  
  # Modo Portfólio com metadados
  python main.py -p meu_projeto -b "Produto" --modo portfolio --metadados
  
  # Analisar website
  python main.py --analisar-site https://exemplo.com
  
  # Analisar Instagram
  python main.py --analisar-instagram @empresa
        """
    )
    
    # Projeto
    parser.add_argument("-p", "--projeto", type=str, default="projeto_default")
    parser.add_argument("-b", "--briefing", type=str)
    parser.add_argument("-n", "--imagens", type=int, default=5)
    parser.add_argument("-m", "--modo", choices=["basic", "pro", "portfolio"], default="basic")
    
    # Metadados
    parser.add_argument("--metadados", action="store_true", help="Adicionar metadados falsos")
    parser.add_argument("--camera", type=str, default="canon_eos",
                       choices=["canon_eos", "nikon_d850", "sony_a7r"],
                       help="Tipo de câmera para metadados")
    
    # Análise
    parser.add_argument("--analisar-site", type=str, help="Analisar website")
    parser.add_argument("--analisar-instagram", type=str, help="Analisar perfil Instagram (@user)")
    
    # Outros
    parser.add_argument("-c", "--continuar", action="store_true")
    parser.add_argument("-r", "--relatorio", action="store_true")
    parser.add_argument("--cache-dir", type=str)
    
    args = parser.parse_args()
    
    # Modo análise de site
    if args.analisar_site:
        modo_analise_site(args)
        return
    
    # Modo análise de Instagram
    if args.analisar_instagram:
        modo_analise_instagram(args)
        return
    
    # Criar orquestrador
    orquestrador = Orquestrador(args.projeto, modo=args.modo)
    
    # Modo relatório
    if args.relatorio:
        relatorio = orquestrador.gerar_relatorio()
        print(relatorio)
        
        caminho = Path("projetos") / args.projeto / "relatorio.md"
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho, "w") as f:
            f.write(relatorio)
        print(f"\n📄 Relatório salvo em: {caminho}")
        return
    
    # Modo continuar
    if args.continuar:
        estado = orquestrador.gerenciador.carregar_estado()
        if estado:
            print(f"📂 Projeto '{args.projeto}' encontrado.")
            print(f"   Modo: {args.modo}")
            print(f"   Etapa: {estado.get('etapa_atual', 'desconhecida')}")
        else:
            print(f"❌ Projeto não encontrado.")
        return
    
    # Verificar briefing
    if not args.briefing:
        parser.error("--briefing é obrigatório. Use -b 'seu briefing'")
    
    # Executar pipeline
    print(f"🚀 Iniciando: {args.projeto}")
    print(f"📝 Briefing: {args.briefing}")
    print(f"🖼️  Imagens: {args.imagens}")
    print(f"⚙️  Modo: {args.modo}")
    if args.metadados:
        print(f"🏷️  Metadados: {args.camera}")
    print("=" * 50)
    
    resultado = orquestrador.executar_pipeline_completo(
        briefing=args.briefing,
        num_imagens=args.imagens
    )
    
    # Mostrar resultado
    print("\n" + "=" * 50)
    print("✅ RESULTADO FINAL")
    print("=" * 50)
    
    estatisticas = resultado.get("estatisticas", {})
    print(f"Imagens aprovadas: {estatisticas.get('total_imagens_aprovadas', 0)}")
    print(f"Imagens rejeitadas: {estatisticas.get('total_imagens_rejeitadas', 0)}")
    
    # Adicionar metadados se solicitado
    adicionar_metadados(args)
    
    # Salvar relatório
    relatorio = orquestrador.gerar_relatorio()
    caminho = Path("projetos") / args.projeto / "relatorio.md"
    with open(caminho, "w") as f:
        f.write(relatorio)
    print(f"\n📄 Relatório: {caminho}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        # Importar aqui para evitar circular
        try:
            from gui import iniciar_interface
            iniciar_interface()
        except ImportError as e:
            print(f"Erro ao iniciar GUI: {e}")
            print("Execute: pip install gradio")
    else:
        main()