"""Renderiza episódios em sequência sem alterar o gerador.py original."""
import argparse
import csv
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml
from PIL import Image, UnidentifiedImageError

BASE = Path(__file__).resolve().parent


def encontrar_roteiro(numero):
    encontrados = sorted((BASE / 'roteiros').glob(f'ep{numero:02d}_*.yaml'))
    if len(encontrados) != 1:
        return None, f'Esperado 1 roteiro ep{numero:02d}_*.yaml; encontrados: {len(encontrados)}'
    return encontrados[0], None


def validar(roteiro):
    erros = []
    try:
        with roteiro.open(encoding='utf-8') as f:
            dados = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        return [f'Falha ao ler YAML: {e}']
    cenas = dados.get('cenas') if isinstance(dados, dict) else None
    if not isinstance(cenas, list) or len(cenas) != 12:
        return [f'Esperadas 12 cenas; encontradas: {len(cenas) if isinstance(cenas, list) else 0}']
    for n, cena in enumerate(cenas, 1):
        if not isinstance(cena, dict):
            erros.append(f'Cena {n}: bloco inválido')
            continue
        for campo in ('imagem', 'narracao', 'movimento'):
            if not isinstance(cena.get(campo), str) or not cena[campo].strip():
                erros.append(f'Cena {n}: {campo} ausente')
        if not isinstance(cena.get('imagem'), str):
            continue
        imagem = (BASE / cena['imagem']).resolve()
        try:
            imagem.relative_to(BASE.resolve())
        except ValueError:
            erros.append(f'Cena {n}: imagem fora do projeto')
            continue
        if imagem.suffix.lower() not in ('.png', '.jpg', '.jpeg') or not imagem.is_file():
            erros.append(f'Cena {n}: imagem inexistente ou extensão inválida: {cena["imagem"]}')
            continue
        try:
            with Image.open(imagem) as im:
                im.load()  # Detecta PNG truncado, não apenas cabeçalho válido.
        except (OSError, ValueError, UnidentifiedImageError) as e:
            erros.append(f'Cena {n}: imagem corrompida: {imagem.name} ({e})')
        if cena.get('movimento') not in ('zoom_in', 'zoom_out', 'estatico'):
            erros.append(f'Cena {n}: movimento inválido')
    return erros


def main():
    p = argparse.ArgumentParser(description='Renderização sequencial de episódios do Bosque Lumiar')
    p.add_argument('--inicio', type=int, required=True)
    p.add_argument('--fim', type=int, required=True)
    p.add_argument('--sobrescrever', action='store_true', help='Renderiza novamente MP4 existentes')
    args = p.parse_args()
    if args.inicio < 1 or args.fim < args.inicio:
        p.error('Informe intervalo válido: --inicio N --fim M (M >= N).')
    pasta_saida = BASE / 'saida'
    pasta_saida.mkdir(parents=True, exist_ok=True)
    pasta_logs = BASE / 'logs'
    pasta_logs.mkdir(parents=True, exist_ok=True)
    resultados = []
    for numero in range(args.inicio, args.fim + 1):
        print(f'\n=== EPISÓDIO {numero:02d} ===', flush=True)
        roteiro, erro = encontrar_roteiro(numero)
        if erro:
            print('ERRO:', erro, flush=True)
            resultados.append((numero, 'ERRO', erro))
            continue
        destino = pasta_saida / f'{roteiro.stem}.mp4'
        if destino.exists() and not args.sobrescrever:
            print('IGNORADO: MP4 já existe (use --sobrescrever para refazer).', flush=True)
            resultados.append((numero, 'IGNORADO', str(destino)))
            continue
        erros = validar(roteiro)
        if erros:
            print('VALIDAÇÃO FALHOU:\n' + '\n'.join(erros), flush=True)
            resultados.append((numero, 'ERRO', '; '.join(erros)))
            continue
        comando = [sys.executable, str(BASE / 'gerador.py'), str(roteiro), '--saida', str(destino)]
        print('Renderizando:', roteiro.name, flush=True)
        log = pasta_logs / f'{roteiro.stem}_{datetime.now():%Y%m%d_%H%M%S}.log'
        with log.open('w', encoding='utf-8') as f:
            processo = subprocess.Popen(comando, cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', bufsize=1)
            for linha in processo.stdout:
                print(linha, end='', flush=True)
                f.write(linha)
            codigo = processo.wait()
        if codigo == 0 and destino.is_file() and destino.stat().st_size > 0:
            print('CONCLUÍDO:', destino.name, flush=True)
            resultados.append((numero, 'OK', str(destino)))
        else:
            detalhe = f'Código {codigo}; consulte {log}'
            print('ERRO:', detalhe, flush=True)
            resultados.append((numero, 'ERRO', detalhe))
    relatorio = pasta_logs / f'relatorio_lote_{datetime.now():%Y%m%d_%H%M%S}.csv'
    with relatorio.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['episodio', 'status', 'detalhes'])
        w.writerows(resultados)
    print('\n=== RESUMO ===', flush=True)
    for numero, status, _ in resultados:
        print(f'Episódio {numero:02d}: {status}', flush=True)
    print('Relatório:', relatorio, flush=True)
    return 1 if any(status == 'ERRO' for _, status, _ in resultados) else 0


if __name__ == '__main__':
    sys.exit(main())
