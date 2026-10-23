# PyVideo Engine

**Automated Video Generation Engine with Python**

PyVideo Engine is a Python-based video generation tool that transforms structured YAML scripts and static images into narrated videos.

The project automates video production by combining text-to-speech, image animation, smooth transitions, and video rendering. It supports individual episode rendering and sequential batch processing.

## Features

- Automated video generation from YAML scripts
- Portuguese text-to-speech using Microsoft Edge TTS
- Audio caching using SHA-256 hashing
- Ken Burns-style camera effects (zoom in and zoom out)
- Smooth transitions between scenes
- Full HD (1920 x 1080) video output at 30 FPS
- H.264 video encoding and AAC audio
- Optimized rendering using Pillow and FFmpeg
- Sequential batch rendering of numbered episodes
- Per-episode error reporting and CSV batch reports
- Option to overwrite existing rendered videos

## Technologies

- Python
- MoviePy
- Pillow
- NumPy
- Edge TTS
- PyYAML
- FFmpeg
- Git

## Project Structure

```text
pyvideo-engine/
├── assets/
│   ├── imagens/         # Scene illustrations
│   └── audios/          # Generated audio cache (ignored by Git)
├── roteiros/            # YAML scripts
├── saida/               # Rendered videos (ignored by Git)
├── logs/                # Batch reports (ignored by Git)
├── gerador.py           # Single-video generator
├── gerador_lote.py      # Batch-rendering command
├── prototipo.py         # Image animation utilities
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

Clone the repository:

```bash
git clone https://github.com/WelisonG/pyvideo-engine.git
cd pyvideo-engine
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

FFmpeg must also be installed and available to the video-rendering environment.

## Usage

### Render a single episode

```cmd
python gerador.py roteiros/ep02_luna_e_a_sementinha_misteriosa.yaml --saida saida/video.mp4
```

The video is saved to the specified output path. If `--saida` is omitted, the generator uses the YAML filename for the MP4 in the `saida/` directory.

### Batch Rendering

The batch renderer finds YAML scripts by episode number using the naming pattern `epNN_*.yaml` inside `roteiros/` and processes the requested range sequentially.

For example, to process episodes 6 through 10:

```cmd
python gerador_lote.py --inicio 6 --fim 10
```

To render existing MP4 files again:

```cmd
python gerador_lote.py --inicio 6 --fim 10 --sobrescrever
```

The batch process reports an error when an episode does not have exactly one matching YAML script. It continues checking subsequent episodes and prints a summary at the end. Execution reports are written to `logs/` as CSV files.

Each YAML script must reference the images needed by the existing single-episode generator. The batch tool reuses `gerador.py` rather than replacing its video rendering pipeline.

**Current validation status:** Command-line help, missing-script handling, and CSV report creation have been tested. Rendering a complete batch of real episodes is still pending.

## Example Project

The engine was developed and tested through *Contos do Bosque Lumiar*, a children's storytelling channel.

It has been used to produce narrated stories with animated illustrations, including camera movements and transitions.

## Future Improvements

- Web interface for video generation
- Additional camera animations
- Background music support
- Automatic subtitle generation
- Configurable video formats and resolutions

## Author

Developed as a Python automation and multimedia processing portfolio project.
