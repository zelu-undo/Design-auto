#!/usr/bin/env python3
"""
Gerenciador de Metadados
Remove metadados de IA e insere metadados falsos para匿名imizar imagens geradas.
Usa piexif para editar EXIF.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# piexif é opcional
try:
    import piexif
    PIEXIF_DISPONIVEL = True
except ImportError:
    PIEXIF_DISPONIVEL = False


class GerenciadorMetadados:
    """Gerencia metadados de imagens."""
    
    # Metadados falsa padrão (como se fosse foto profissional)
    METADADOS_CAMERA = {
        "Make": "Canon",           # Fabricante
        "Model": "Canon EOS 5D Mark IV",  # Modelo de câmera
        "Software": "Adobe Photoshop Lightroom 6",  # Software de edição
        "DateTime": "",            # Data da criação
        "DateTimeOriginal": "",     # Data original
        "DateTimeDigitized": "",   # Data de digitalização
    }
    
    # Lente padrão
    LENTE = {
        "LensModel": "EF 50mm f/1.4L USM",
        "LensMake": "Canon",
        "FocalLength": "50",
        "FNumber": "1.4",
        "ExposureTime": "1/250",
        "ISOSpeedRatings": "100",
        "Flash": "No Flash",
    }
    
    # Localização (opcional)
    LOCAL = {
        "GPSLatitude": "0",
        "GPSLatitudeRef": "N",
        "GPSLongitude": "0",
        "GPSLongitudeRef": "W",
    }
    
    def verificar_piexif(self) -> bool:
        """Verifica se piexif está disponível."""
        if not PIEXIF_DISPONIVEL:
            print("⚠️ piexif não disponível. Execute: pip install piexif")
        return PIEXIF_DISPONIVEL
    
    def _criar_exif_vazio(self) -> dict:
        """Cria estrutura EXIF vazia."""
        return {
            "0th": {},
            "Exif": {},
            "GPS": {},
            "1st": {},
            "thumbnail": None
        }
    
    def _criar_exif_falso(
        self,
        data: Optional[str] = None,
        usar_lente: bool = True,
        usar_local: bool = False
    ) -> bytes:
        """
        Cria metadados EXIF falsos.
        
        Args:
            data: Data no formato "YYYY:MM:DD HH:MM:SS"
            usar_lente: Incluir informações de lente
            usar_local: Incluir localização GPS
            
        Returns:
            Bytes do EXIF
        """
        if not self.verificar_piexif():
            return b""
        
        if data is None:
            from datetime import datetime
            data = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
        
        exif_dict = self._criar_exif_vazio()
        
        # 0th IFD - Informações básicas
        exif_dict["0th"] = {
            piexif.ImageIFD.Make: "Canon",
            piexif.ImageIFD.Model: "Canon EOS 5D Mark IV",
            piexif.ImageIFD.Software: "Adobe Photoshop Lightroom 6",
        }
        
        # Exif IFD - Informações de exposição
        exif_dict["Exif"] = {
            piexif.ExifIFD.DateTimeOriginal: data,
            piexif.ExifIFD.DateTimeDigitized: data,
            piexif.ExifIFD.ExposureTime: (1, 250),
            piexif.ExifIFD.FNumber: (14, 10),  # f/1.4
            piexif.ExifIFD.ISOSpeedRatings: 100,
            piexif.ExifIFD.Flash: b'\x00',
            piexif.ExifIFD.LensModel: "EF 50mm f/1.4L USM",
            piexif.ExifIFD.LensMake: "Canon",
            piexif.ExifIFD.FocalLength: (50, 1),
        }
        
        # GPS IFD (se solicitado)
        if usar_local:
            from piexif import GPSIFD
            exif_dict["GPS"] = {
                GPSIFD.GPSLatitudeRef: b'N',
                GPSIFD.GPSLatitude: ((40, 1), (40, 1), (4000, 100)),
                GPSIFD.GPSLongitudeRef: b'W',
                GPSIFD.GPSLongitude: ((74, 1), (0, 1), (6000, 100)),
            }
        
        return piexif.dump(exif_dict)
    
    def limpar_metadados(
        self,
        caminho_imagem: str,
        modo_profissional: bool = True,
        data: Optional[str] = None,
        usar_lente: bool = True,
        usar_local: bool = False
    ) -> Tuple[bool, str]:
        """
        Remove metadados de IA e insere metadados falsos.
        
        Args:
            caminho_imagem: Caminho da imagem
            modo_professional: SeTrue, insere metadados falsos de câmera profissional
            data: Data personalizada
            usar_lente: Incluir informações de lente
            usar_local: Incluir GPS
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        if not self.verificar_piexif():
            return False, "piexif não disponível"
        
        caminho = Path(caminho_imagem)
        if not caminho.exists():
            return False, f"Arquivo não encontrado: {caminho_imagem}"
        
        try:
            # Converter para RGB se necessário
            from PIL import Image
            img = Image.open(caminho)
            
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            
            # Gerar EXIF falso ou vazio
            if modo_profissional:
                exif_bytes = self._criar_exif_falso(
                    data=data,
                    usar_lente=usar_lente,
                    usar_local=usar_local
                )
            else:
                exif_bytes = b""
            
            # Salvar imagem sem metadados originais
            img.save(caminho, "JPEG", exif=exif_bytes, quality=95)
            
            return True, "Metadados processados"
            
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def processar_batch(
        self,
        caminhos: list,
        modo_professional: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Processa múltiplas imagens.
        
        Args:
            caminhos: Lista de caminhos
            modo_professional: Modo profissional
            **kwargs: Outros argumentos
            
        Returns:
            Estatísticas do processamento
        """
        sucessos = 0
        erros = 0
        
        for caminho in caminhos:
            sucesso, _ = self.limpar_metadados(
                caminho,
                modo_professional,
                **kwargs
            )
            if sucesso:
                sucessos += 1
            else:
                erros += 1
        
        return {
            "total": len(caminhos),
            "sucessos": sucessos,
            "erros": erros
        }
    
    def verificar_metadados(self, caminho_imagem: str) -> Dict[str, Any]:
        """Verifica metadados existentes na imagem."""
        if not self.verificar_piexif():
            return {}
        
        try:
            from PIL import Image
            exif_data = Image.open(caminho_imagem).getexif()
            
            metadados = {}
            for tag_id, value in exif_data.items():
                metadados[tag_id] = value
            
            return metadados
            
        except Exception:
            return {}
    
    def remover_todos_metadados(self, caminho_imagem: str) -> bool:
        """Remove todos os metadados da imagem."""
        try:
            from PIL import Image
            img = Image.open(caminho_imagem)
            
            # Converter para RGB
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # Salvar sem EXIF
            img.save(caminho_imagem, "JPEG")
            
            return True
            
        except Exception:
            return False


class MetadadosOpcoes:
    """Opções de metadados pré-definidas."""
    
    # Estilos de câmera
    CANON_EOS = {
        "make": "Canon",
        "model": "Canon EOS 5D Mark IV",
        "lente": "EF 50mm f/1.4L USM"
    }
    
    NIKON_D850 = {
        "make": "Nikon",
        "model": "Nikon D850",
        "lente": "NIKKOR 50mm f/1.4G"
    }
    
    SONY_A7R = {
        "make": "Sony",
        "model": "Sony A7R IV",
        "lente": "FE 50mm f/1.4 GM"
    }
    
    # Editores
    PHOTOSHOP = {
        "software": "Adobe Photoshop Lightroom 6"
    }
    
    CAPTURE_ONE = {
        "software": "Capture One Pro 21"
    }
    
    @classmethod
    def get_opcoes(cls) -> Dict[str, Dict]:
        """Retorna todas as opções disponíveis."""
        return {
            "cameras": {
                "canon_eos": cls.CANON_EOS,
                "nikon_d850": cls.NIKON_D850,
                "sony_a7r": cls.SONY_A7R
            },
            "editores": {
                "photoshop": cls.PHOTOSHOP,
                "capture_one": cls.CAPTURE_ONE
            }
        }