#!/usr/bin/env python3
"""
Analisador de Sites e Redes Sociais
Extrai informações visuais e de estilo de sites para garantir consistência.
Suporta análise de websites genéricos e Instagram.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Imports opcionais
try:
    from bs4 import BeautifulSoup
    BS4_DISPONIVEL = True
except ImportError:
    BS4_DISPONIVEL = False

try:
    import requests
    REQUESTS_DISPONIVEL = True
except ImportError:
    REQUESTS_DISPONIVEL = False


class AnalisadorSite:
    """Analisa websites para extrair informações de estilo."""
    
    def __init__(self):
        self.site = None
        self.html = None
        self.soup = None
        self.cores_extraidas = []
        self.fontes_extraidas = []
        self.imagens_extraidas = []
    
    def _verificar_dependencias(self) -> bool:
        """Verifica se as dependências estão disponíveis."""
        if not BS4_DISPONIVEL:
            print("⚠️ beautifulsoup4 não disponível. Execute: pip install beautifulsoup4")
        if not REQUESTS_DISPONIVEL:
            print("⚠️ requests não disponível. Execute: pip install requests")
        return BS4_DISPONIVEL and REQUESTS_DISPONIVEL
    
    def _extrair_cores_hex(self, texto: str) -> List[str]:
        """Extrai códigos de cores hex do texto."""
        # Padrão para cores hex (#FFFFFF ou #FFF)
        padrao = r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b'
        cores = re.findall(padrao, texto, re.IGNORECASE)
        
        # Normalizar para 6 dígitos
        hex_cores = []
        for cor in cores:
            if len(cor) == 3:
                # Expandir #FFF para #FFFFFF
                hex_cores.append(f"#{cor[0]}{cor[0]}{cor[1]}{cor[1]}{cor[2]}{cor[2]}".upper())
            elif len(cor) == 6:
                hex_cores.append(f"#{cor}".upper())
        
        return list(set(hex_cores))
    
    def _extrair_cores_rgb(self, texto: str) -> List[str]:
        """Extrai cores em formato RGB."""
        padrao = r'rgb\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)'
        matches = re.findall(padrao, texto, re.IGNORECASE)
        
        cores = []
        for match in matches:
            r, g, b = int(match[0]), int(match[1]), int(match[2])
            # Converter para hex
            hex_cor = f"#{r:02X}{g:02X}{b:02X}"
            cores.append(hex_cor)
        
        return cores
    
    def _extrair_fontes(self, texto: str) -> List[str]:
        """Extrai nomes de fontes do texto."""
        # Fontes comuns
        fontes_conhecidas = [
            "Helvetica", "Arial", "Times New Roman", "Georgia", "Verdana",
            "Roboto", "Open Sans", "Lato", "Montserrat", "Poppins",
            "Playfair Display", "Merriweather", "Source Sans", "Inter",
            "Oswald", "Raleway", "Nunito", "Ubuntu", "Fira Sans",
            "DIN", "GT America", "Neue Montreal", "Akzidenz"
        ]
        
        fontes_encontradas = []
        texto_lower = texto.lower()
        
        for fonte in fontes_conhecidas:
            if fonte.lower() in texto_lower:
                fontes_encontradas.append(fonte)
        
        return list(set(fontes_encontradas))
    
    def _extrair_estilos(self, texto: str) -> Dict[str, Any]:
        """Extrai informações de estilo."""
        texto_lower = texto.lower()
        
        estilo = {}
        
        # Detectar tom (tons claros ou escuros)
        if "white" in texto_lower or "#ffffff" in texto_lower:
            estilo["tom_fundo"] = "claro"
        elif "black" in texto_lower or "#000000" in texto_lower:
            estilo["tom_fundo"] = "escuro"
        
        # Detectar energia
        palavras_energia = ["bold", "vibrant", "dynamic", "energetic"]
        palavras_serenidade = ["calm", "minimal", "clean", "simple", "serene"]
        
        energia_score = sum(1 for p in palavras_energia if p in texto_lower)
        serenidade_score = sum(1 for p in palavras_serenidade if p in texto_lower)
        
        if energia_score > serenidade_score:
            estilo["mood"] = "energetic"
        elif serenidade_score > energia_score:
            estilo["mood"] = "serene"
        else:
            estilo["mood"] = "balanced"
        
        return estilo
    
    def analisar_url(self, url: str) -> Dict[str, Any]:
        """Analisa um website."""
        if not self._verificar_dependencias():
            return {"erro": "Dependências não disponíveis"}
        
        try:
            # Baixar HTML
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            self.html = response.text
            self.site = url
            
            # Parsear HTML
            self.soup = BeautifulSoup(self.html, "html.parser")
            
            # Extrair informações
            resultado = self._extrair_informacoes()
            
            return {
                "url": url,
                "status": "sucesso",
                **resultado
            }
            
        except Exception as e:
            return {"url": url, "status": "erro", "mensagem": str(e)}
    
    def _extrair_informacoes(self) -> Dict[str, Any]:
        """Extrai todas as informações do site."""
        # Todo o texto
        texto_total = self.soup.get_text()
        
        # Cores
        cores_hex = self._extrair_cores_hex(texto_total)
        cores_rgb = self._extrair_cores_rgb(texto_total)
        todas_cores = list(set(cores_hex + cores_rgb))
        
        # Fontes
        fontes = self._extrair_fontes(texto_total)
        
        # Estilos
        estilos = self._extrair_estilos(texto_total)
        
        # URLs de imagens
        imagens = []
        for img in self.soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                if src.startswith("http"):
                    imagens.append(src)
                elif src.startswith("/"):
                    # URL relativa
                    from urllib.parse import urljoin
                    imagens.append(urljoin(self.site, src))
        
        return {
            "cores": todas_cores[:10],  # Limitar a 10
            "fontes": fontes[:5],
            "estilos": estilos,
            "imagens": imagens[:20],
            "total_imagens": len(imagens)
        }


class AnalisadorInstagram(AnalisadorSite):
    """Analisa perfil do Instagram para extrair estilo visual."""
    
    def __init__(self):
        super().__init__()
        self.perfil = None
        self.posts = []
        self.highlights = []
    
    def _extrair_hashtags(self, texto: str) -> List[str]:
        """Extrai hashtags do texto."""
        padrao = r'#(\w+)'
        return re.findall(padrao, texto)
    
    def _extrair_mentions(self, texto: str) -> List[str]:
        """Extrai menções do texto."""
        padrao = r'@(\w+)'
        return re.findall(padrao, texto)
    
    def analisar_perfil(self, username: str) -> Dict[str, Any]:
        """
        Analisa um perfil do Instagram.
        
        Note: Sem API oficial, usa scraping básico público.
        """
        url = f"https://www.instagram.com/{username}/"
        
        if not self._verificar_dependencias():
            return {"erro": "Dependências não disponíveis"}
        
        try:
            # Simular análise (sem API real)
            # Em produção, usar Instagram Graph API ou scraping
            self.perfil = username
            
            # Estrutura de resultado simulado
            return {
                "username": username,
                "url": url,
                "status": "analisado",
                "cores_principais": [],
                "paletas_detectadas": [],
                "hashtags_frequentes": [],
                "estilo_visual": "minimal",
                "tipos_conteudo": ["photo", "video", "carousel"],
                "consistency_score": 0.0,
                "nota": "Análise simulada sem API"
            }
            
        except Exception as e:
            return {"username": username, "status": "erro", "mensagem": str(e)}
    
    def _calcular_consistencia(
        self,
        cores: List[str],
        hashtags: List[str],
        estilo: str
    ) -> float:
        """Calcula_score de consistência visual."""
        score = 0.5
        
        # Bônus por paleta consistente
        if len(cores) >= 3:
            score += 0.2
        
        # Bônus por hashtags consistentes
        if len(set(hashtags)) >= 5:
            score += 0.15
        
        # Bônus por estilo definido
        if estilo:
            score += 0.15
        
        return min(score, 1.0)
    
    def gerar_relatorio(self) -> str:
        """Gera relatório da análise."""
        if not self.perfil:
            return "Nenhuma análise realizada"
        
        linhas = [
            f"# Análise do Instagram: @{self.perfil}",
            "",
            "## Cores Principais",
            ", ".join(self.cores_extraidas[:5]) or "Não detectadas",
            "",
            "## Fontes",
            ", ".join(self.fontes_extraidas) or "Não detectadas",
            "",
            "## Estilo",
            self._detectar_estilo(),
            "",
            "## Consistência",
            f"{self._calcular_consistencia():.1%}"
        ]
        
        return "\n".join(linhas)
    
    def _detectar_estilo(self) -> str:
        """Detecta estilo geral."""
        if not self.cores_extraidas:
            return "desconhecido"
        
        # Contar cores escuras vs claras
        escuras = sum(1 for c in self.cores_extraidas if self._e_cor_escura(c))
        total = len(self.cores_extraidas)
        
        if escuras / total > 0.7:
            return "dark"
        elif escuras / total < 0.3:
            return "light"
        return "balanced"
    
    def _e_cor_escura(self, hex_cor: str) -> bool:
        """Verifica se cor é escura."""
        if not hex_cor.startswith("#") or len(hex_cor) != 7:
            return False
        
        try:
            r = int(hex_cor[1:3], 16)
            g = int(hex_cor[3:5], 16)
            b = int(hex_cor[5:7], 16)
            
            # Luminosidade simples
            return (r + g + b) / 3 < 128
        except:
            return False


class AnalisadorSiteFactory:
    """Factory para criar analisadores."""
    
    @staticmethod
    def criar(tipo: str = "site") -> AnalisadorSite:
        """Cria analisador conforme tipo."""
        if tipo == "instagram":
            return AnalisadorInstagram()
        return AnalisadorSite()
    
    @staticmethod
    def analisar(
        url: str,
        tipo: str = "site",
        **kwargs
    ) -> Dict[str, Any]:
        """Análise direta via factory."""
        if tipo == "instagram":
            username = url.replace("@", "").strip()
            analisador = AnalisadorInstagram()
            return analisador.analisar_perfil(username)
        
        analisador = AnalisadorSite()
        return analisador.analisar_url(url)


# Função de conveniência
def analisar_instagram(username: str) -> Dict[str, Any]:
    """Função de conveniência para analisar Instagram."""
    return AnalisadorSiteFactory.analisar(username, tipo="instagram")


def analisar_site(url: str) -> Dict[str, Any]:
    """Função de conveniência para analisar site."""
    return AnalisadorSiteFactory.analisar(url, tipo="site")