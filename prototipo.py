"""Protótipo do Contos do Bosque Lumiar: uma cena com narração, exportada em MP4 1920x1080."""

import asyncio
import math
import tempfile
from pathlib import Path

import edge_tts
import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
IMAGEM = BASE_DIR / "assets" / "imagens" / "a_vibrant_cute_colorful_2d_cartoon_illustration.png"
SAIDA = BASE_DIR / "saida" / "prototipo_v3.mp4"

LARGURA, ALTURA, FPS = 1920, 1080, 30
VOZ = "pt-BR-FranciscaNeural"
VELOCIDADE = "-5%"
TEXTO = (
    "Em uma linda manhã, Léo passeava alegremente pelo Bosque Lumiar, "
    "quando algo chamou sua atenção."
)
ZOOM_INICIAL, ZOOM_FINAL = 1.00, 1.15


def gerar_narracao(caminho: Path) -> None:
    """Gera a narração pt-BR com edge-tts e salva em MP3."""
    communicate = edge_tts.Communicate(TEXTO, VOZ, rate=VELOCIDADE)
    asyncio.run(communicate.save(str(caminho)))


def preparar_quadro(caminho_imagem: Path) -> Image.Image:
    """Encaixa a imagem no quadro 16:9 sem distorcer, preenchendo as sobras com a cor da borda."""
    original = Image.open(caminho_imagem).convert("RGB")
    cor_fundo = original.getpixel((0, 0))

    escala = min(LARGURA / original.width, ALTURA / original.height)
    nova_largura = round(original.width * escala)
    nova_altura = round(original.height * escala)
    ajustada = original.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)

    quadro = Image.new("RGB", (LARGURA, ALTURA), cor_fundo)
    quadro.paste(ajustada, ((LARGURA - nova_largura) // 2, (ALTURA - nova_altura) // 2))
    return quadro


def curva_suave(progresso: float) -> float:
    """Ease-in-out por cosseno: começa e termina parado, com movimento contínuo no meio."""
    return 0.5 - 0.5 * math.cos(math.pi * progresso)


def criar_cena(quadro: Image.Image, duracao: float) -> VideoClip:
    """Cria a cena com zoom subpixel: cada quadro recorta uma janela fracionária e a reamostra com BICUBIC."""

    def gerar_quadro(t: float) -> np.ndarray:
        progresso = min(t / duracao, 1.0)
        zoom = ZOOM_INICIAL + (ZOOM_FINAL - ZOOM_INICIAL) * curva_suave(progresso)

        janela_largura = LARGURA / zoom
        janela_altura = ALTURA / zoom
        x0 = (LARGURA - janela_largura) / 2
        y0 = (ALTURA - janela_altura) / 2

        transformacao = (
            janela_largura / LARGURA, 0, x0,
            0, janela_altura / ALTURA, y0,
        )
        recorte = quadro.transform(
            (LARGURA, ALTURA),
            Image.Transform.AFFINE,
            transformacao,
            resample=Image.Resampling.BICUBIC,
        )
        return np.asarray(recorte)

    return VideoClip(frame_function=gerar_quadro, duration=duracao)


def main() -> None:
    SAIDA.parent.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as temp:
        narracao = Path(temp) / "narracao.mp3"
        gerar_narracao(narracao)

        audio = AudioFileClip(str(narracao))
        duracao = audio.duration

        video = criar_cena(preparar_quadro(IMAGEM), duracao).with_audio(audio)

        video.write_videofile(str(SAIDA), fps=FPS, codec="libx264", audio_codec="aac")

        video.close()
        audio.close()


if __name__ == "__main__":
    main()
