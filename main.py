#!/usr/bin/env python3
"""
ArtisanAI Studio - Ponto de Entrada

Uso simples:
    python main.py -p meu_projeto -b "Fashion moderna"
    
Modos de operação:
    --modo basic      (padrão)    SDXL-Turbo, avaliação automática
    --modo pro                   Flux.1 Schnell, revisão manual via Gradio
    --modo portfolio             Flux.1 Schnell, avaliação rigorosa automática
"""

import argparse
import sys
from pathlib import Path

# Adicionar pasta atual ao path
sys.path.insert(0, str(Path(__file__).parent))

# Importar módulos do pacote
try:
    from src import Orquestrador
except ImportError as e:
    print(f"Erro ao importar: {e}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="🏭 ArtisanAI Studio - Fábrica de Design Autônoma",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # Modo Básico (padrão) - SDXL-Turbo
  python main.py -p meu_projeto -b "Fashion moderna"
  
  # Modo Profissional - Flux.1 Schnell + Revisão Manual
  python main.py -p meu_projeto -b "Logo startup" --modo pro
  
  # Modo Portfólio - Automação de Alta Qualidade
  python main.py -p meu_projeto -b "Produto natural" --modo portfolio
  
  # Continuar projeto existente
  python main.py --continuar -p meu_projeto
  
  # Gerar relatório
  python main.py -r -p meu_projeto
        """
    )
    parser.add_argument(
        "-p", "--projeto",
        type=str,
        default="projeto_default",
        help="Nome do projeto (padrão: projeto_default)"
    )
    parser.add_argument(
        "-b", "--briefing",
        type=str,
        help="Briefing do projeto (obrigatório para novo projeto)"
    )
    parser.add_argument(
        "-n", "--imagens",
        type=int,
        default=5,
        help="Número de imagens desejadas (padrão: 5)"
    )
    parser.add_argument(
        "-m", "--modo",
        type=str,
        choices=["basic", "pro", "portfolio"],
        default="basic",
        help="Modo de operação (padrão: basic)"
    )
    parser.add_argument(
        "-c", "--continuar",
        action="store_true",
        help="Continuar projeto existente"
    )
    parser.add_argument(
        "-r", "--relatorio",
        action="store_true",
        help="Gerar relatório do projeto"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        help="Diretório de cache dos modelos (opcional)"
    )
    
    args = parser.parse_args()
    
    # Criar orquestrador com modo
    orquestrador = Orquestrador(args.projeto, modo=args.modo)
    
    # Modo relatório
    if args.relatorio:
        relatorio = orquestrador.gerar_relatorio()
        print(relatorio)
        
        # Salvar relatório
        caminho_relatorio = Path("projetos") / args.projeto / "relatorio.md"
        caminho_relatorio.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho_relatorio, "w") as f:
            f.write(relatorio)
        print(f"\n📄 Relatório salvo em: {caminho_relatorio}")
        return
    
    # Modo continuar
    if args.continuar:
        estado = orquestrador.gerenciador.carregar_estado()
        if estado:
            print(f"📂 Projeto '{args.projeto}' encontrado.")
            print(f"   Modo: {args.modo}")
            print(f"   Etapa atual: {estado.get('etapa_atual', 'desconhecida')}")
            
            # Verificar progresso
            progresso = orquestrador.get_progresso()
            print(f"   Progresso: {progresso*100:.1f}%")
            
            estatisticas = orquestrador.gerenciador.get_estatisticas()
            print(f"   Imagens aprovadas: {estatisticas.get('total_imagens_aprovadas', 0)}")
            print(f"   Imagens rejeitadas: {estatisticas.get('total_imagens_rejeitadas', 0)}")
            
            # Verificar etapa atual e continuar
            etapa = estado.get("etapa_atual", "inicializado")
            
            if etapa in ["inicializado", "style_guide_pronto"]:
                print("\n🚀 Executando pipeline...")
                
                briefing = args.briefing or estado.get("briefing", "")
                if not briefing:
                    print("❌ Briefing não encontrado. Forneça com --briefing")
                    return
                
                resultado = orquestrador.executar_pipeline_completo(
                    briefing=briefing,
                    num_imagens=args.imagens
                )
                
                # Mostrar resultado
                print("\n" + "=" * 50)
                print("✅ RESULTADO FINAL")
                print("=" * 50)
                
                estatisticas = resultado.get("estatisticas", {})
                print(f"Imagens aprovadas: {estatisticas.get('total_imagens_aprovadas', 0)}")
                print(f"Imagens rejeitadas: {estatisticas.get('total_imagens_rejeitadas', 0)}")
            else:
                print("⚠️ Projeto já está completo ou em andamento.")
        else:
            print(f"❌ Projeto '{args.projeto}' não encontrado.")
            print("   Crie um novo projeto com --briefing")
        return
    
    # Verificar briefing
    if not args.briefing:
        parser.error("--briefing é obrigatório para novos projetos. Use -b 'seu briefing'")
    
    # Executar pipeline completo
    print(f"🚀 Iniciando projeto: {args.projeto}")
    print(f"📝 Briefing: {args.briefing}")
    print(f"🖼️  Imagens desejadas: {args.imagens}")
    print(f"⚙️  Modo: {args.modo}")
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
    
    metricas = estatisticas.get("metricas_media", {})
    if metricas:
        print(f"\n📊 Métricas médias:")
        print(f"   CLIP: {metricas.get('clip', 0):.2f}")
        print(f"   Aesthetic: {metricas.get('aesthetic', 0):.1f}")
        print(f"   BRISQUE: {metricas.get('brisque', 0):.1f}")
    
    # Salvar relatório
    relatorio = orquestrador.gerar_relatorio()
    caminho_relatorio = Path("projetos") / args.projeto / "relatorio.md"
    caminho_relatorio.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_relatorio, "w") as f:
        f.write(relatorio)
    print(f"\n📄 Relatório salvo em: {caminho_relatorio}")


if __name__ == "__main__":
    main()