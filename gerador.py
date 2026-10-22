"""Gerador de vídeos multicenas do Contos do Bosque Lumiar a partir de um roteiro YAML."""

import argparse
import asyncio
import sys
import tempfile
import hashlib
from pathlib import Path

import edge_tts
import numpy as np
import yaml
from moviepy import AudioFileClip, CompositeVideoClip, VideoClip, concatenate_audioclips, vfx
from PIL import Image

from prototipo import ALTURA, BASE_DIR, FPS, LARGURA, VELOCIDADE, VOZ, curva_suave, preparar_quadro

ZOOM_MAXIMO = 1.15
MOVIMENTOS = {
    "zoom_in": (1.00, ZOOM_MAXIMO),
    "zoom_out": (ZOOM_MAXIMO, 1.00),
    "estatico": (1.00, 1.00),
}
CAMPOS_OBRIGATORIOS = ("imagem", "narracao", "movimento")
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg"}
TRANSICAO = 0.5
METADE_TRANSICAO = TRANSICAO / 2


def validar_cena(numero: int, cena: object) -> list[str]:
    """Retorna os erros encontrados em uma cena, sem gerar nada."""
    if not isinstance(cena, dict):
        return [f"Cena {numero}: deve ser um bloco com os campos {', '.join(CAMPOS_OBRIGATORIOS)}."]

    erros = []
    for campo in CAMPOS_OBRIGATORIOS:
        valor = cena.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            erros.append(f"Cena {numero}: campo obrigatório ausente ou vazio: '{campo}'.")
    if erros:
        return erros

    imagem = BASE_DIR / cena["imagem"]
    if imagem.suffix.lower() not in EXTENSOES_IMAGEM:
        erros.append(f"Cena {numero}: formato de imagem não suportado: {cena['imagem']}")
    elif not imagem.is_file():
        erros.append(f"Cena {numero}: imagem não encontrada: {cena['imagem']}")

    if cena["movimento"] not in MOVIMENTOS:
        opcoes = ", ".join(MOVIMENTOS)
        erros.append(f"Cena {numero}: movimento inválido '{cena['movimento']}'. Use: {opcoes}.")

    return erros


def carregar_roteiro(caminho: Path) -> list[dict]:
    """Lê o roteiro YAML e valida todas as cenas antes de gerar qualquer áudio ou vídeo."""
    with caminho.open(encoding="utf-8") as arquivo:
        dados = yaml.safe_load(arquivo)

    if not isinstance(dados, dict) or not isinstance(dados.get("cenas"), list) or not dados["cenas"]:
        raise ValueError("O roteiro precisa ter uma lista não vazia chamada 'cenas'.")

    erros = []
    for numero, cena in enumerate(dados["cenas"], start=1):
        erros.extend(validar_cena(numero, cena))
    if erros:
        raise ValueError("\n".join(erros))

    return dados["cenas"]


def gerar_narracao(texto: str, caminho: Path) -> None:
    """Reutiliza narrações existentes ou gera um novo MP3."""

    pasta_cache = BASE_DIR / "assets" / "audios"
    pasta_cache.mkdir(parents=True, exist_ok=True)

    identificador = hashlib.sha256(
        f"{VOZ}|{VELOCIDADE}|{texto}".encode("utf-8")
    ).hexdigest()

    arquivo_cache = pasta_cache / f"{identificador}.mp3"

    if arquivo_cache.is_file() and arquivo_cache.stat().st_size > 0:
        print("Narração reutilizada do cache.")
    else:
        print("Gerando nova narração...")
        communicate = edge_tts.Communicate(texto, VOZ, rate=VELOCIDADE)
        asyncio.run(communicate.save(str(arquivo_cache)))

    import shutil
    shutil.copyfile(arquivo_cache, caminho)


def calcular_zoom(t: float, duracao_clipe: float, zoom_inicial: float, zoom_final: float) -> float:
    """Zoom no instante t do clipe, com curva ease-in-out ao longo de toda a duração visual."""
    progresso = min(max(t / duracao_clipe, 0.0), 1.0)
    return zoom_inicial + (zoom_final - zoom_inicial) * curva_suave(progresso)


def criar_cena_com_movimento(
    quadro: Image.Image,
    duracao_clipe: float,
    zoom_inicial: float,
    zoom_final: float,
) -> VideoClip:
    """Cria a cena com zoom subpixel e curva ease-in-out, a mesma técnica do protótipo aprovado.

    O movimento cobre toda a duração visual do clipe, incluindo as extensões das transições,
    então a cena não para antes do fim do próprio clipe.
    """

    def gerar_quadro(t: float):
        zoom = calcular_zoom(t, duracao_clipe, zoom_inicial, zoom_final)

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
            resample=Image.Resampling.BILINEAR,
        )
        return np.asarray(recorte)

    return VideoClip(frame_function=gerar_quadro, duration=duracao_clipe)


def validar_transicoes(duracoes: list[float]) -> None:
    """Confere se cada narração é longa o bastante para receber duas transições sem sobreposição."""
    if len(duracoes) < 2:
        return
    for numero, duracao in enumerate(duracoes, start=1):
        if duracao < TRANSICAO:
            raise ValueError(
                f"Cena {numero}: narração com {duracao:.2f} s é curta demais para a transição de "
                f"{TRANSICAO} s. Use pelo menos {TRANSICAO} s por cena."
            )


def montar_video(cenas: list[dict], saida: Path) -> None:
    """Gera as narrações em sequência e monta as imagens com transições centradas nos cortes."""
    with tempfile.TemporaryDirectory() as temp:
        audios = []
        for numero, cena in enumerate(cenas, start=1):
            narracao = Path(temp) / f"narracao_{numero:02d}.mp3"
            gerar_narracao(cena["narracao"], narracao)
            audios.append(AudioFileClip(str(narracao)))

        try:
            duracoes = [audio.duration for audio in audios]
            validar_transicoes(duracoes)

            total = sum(duracoes)
            clipes = []
            inicio_narracao = 0.0

            for numero, (cena, duracao) in enumerate(zip(cenas, duracoes), start=1):
                fim_narracao = inicio_narracao + duracao

                inicio_visual = max(0.0, inicio_narracao - METADE_TRANSICAO) if numero > 1 else 0.0
                fim_visual = min(total, fim_narracao + METADE_TRANSICAO) if numero < len(cenas) else total

                zoom_inicial, zoom_final = MOVIMENTOS[cena["movimento"]]
                quadro = preparar_quadro(BASE_DIR / cena["imagem"])
                clipe = criar_cena_com_movimento(
                    quadro,
                    duracao_clipe=fim_visual - inicio_visual,
                    zoom_inicial=zoom_inicial,
                    zoom_final=zoom_final,
                ).with_start(inicio_visual)

                if numero > 1:
                    clipe = clipe.with_effects([vfx.CrossFadeIn(TRANSICAO)])

                clipes.append(clipe)
                inicio_narracao = fim_narracao

            video = CompositeVideoClip(clipes, size=(LARGURA, ALTURA)).with_duration(total)
            narracao_total = concatenate_audioclips(audios)
            video = video.with_audio(narracao_total)

            video.write_videofile(
                 str(saida),
                 fps=FPS,
                 codec="libx264",
                 audio_codec="aac",
                 preset="veryfast",
                 threads=4,
            )       

            video.close()
            narracao_total.close()
        finally:
            for audio in audios:
                audio.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera um MP4 multicenas a partir de um roteiro YAML.")
    parser.add_argument("roteiro", type=Path, help="Caminho do roteiro YAML, relativo à raiz do projeto.")
    parser.add_argument(
        "--saida",
        type=Path,
        help="Caminho do MP4 de saída, relativo à raiz do projeto. Padrão: saida/<nome-do-roteiro>.mp4.",
    )
    args = parser.parse_args()

    roteiro = args.roteiro if args.roteiro.is_absolute() else BASE_DIR / args.roteiro
    if not roteiro.is_file():
        print(f"Roteiro não encontrado: {roteiro}", file=sys.stderr)
        sys.exit(1)

    try:
        cenas = carregar_roteiro(roteiro)
    except (ValueError, yaml.YAMLError) as erro:
        print(f"Roteiro inválido:\n{erro}", file=sys.stderr)
        sys.exit(1)

    if args.saida:
        saida = args.saida if args.saida.is_absolute() else BASE_DIR / args.saida
    else:
        saida = BASE_DIR / "saida" / f"{roteiro.stem}.mp4"
    saida.parent.mkdir(exist_ok=True)

    try:
        montar_video(cenas, saida)
    except ValueError as erro:
        print(f"Roteiro inválido:\n{erro}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
