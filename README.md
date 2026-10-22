\# PyVideo Engine



\*\*Automated Video Generation Engine with Python\*\*



PyVideo Engine is a Python-based video generation tool that transforms structured YAML scripts and static images into narrated videos.



The project automates video production by combining text-to-speech, image animation, smooth transitions and video rendering.



\## Features



\- Automated video generation from YAML scripts

\- Portuguese text-to-speech using Microsoft Edge TTS

\- Audio caching using SHA-256 hashing

\- Ken Burns-style camera effects (zoom in and zoom out)

\- Smooth transitions between scenes

\- Full HD (1920 × 1080) video output at 30 FPS

\- H.264 video encoding and AAC audio

\- Optimized rendering using Pillow and FFmpeg



\## Technologies



\- Python

\- MoviePy

\- Pillow

\- NumPy

\- Edge TTS

\- PyYAML

\- FFmpeg

\- Git



\## Project Structure



```text

pyvideo-engine/

├── assets/

│   ├── imagens/

│   └── audios/          # Generated audio cache (ignored by Git)

├── roteiros/            # YAML scripts

├── saida/               # Rendered videos (ignored by Git)

├── gerador.py           # Main video generator

├── prototipo.py         # Image animation utilities

├── requirements.txt

├── .gitignore

└── README.md

```



\## Installation



Clone the repository:



```bash

git clone https://github.com/YOUR\_USERNAME/pyvideo-engine.git

cd pyvideo-engine

```



Create a Python virtual environment:



```bash

python -m venv .venv

```



Activate it on Windows:



```cmd

.venv\\Scripts\\activate

```



Install dependencies:



```bash

pip install -r requirements.txt

```



\## Usage



Generate a video using a YAML script:



```bash

python gerador.py roteiros/ep02\_luna\_e\_a\_sementinha\_misteriosa.yaml --saida saida/video.mp4

```



The generated video will be saved in the specified output directory.



\## Example Project



The engine was developed and tested through \*Contos do Bosque Lumiar\*, a children's storytelling channel.



It has been used to produce narrated stories with animated illustrations, including camera movements and transitions.



\## Future Improvements



\- Web interface for video generation

\- Additional camera animations

\- Background music support

\- Automatic subtitle generation

\- Configurable video formats and resolutions



\## Author



Developed as a Python automation and multimedia processing portfolio project.

