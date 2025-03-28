FROM mtgupf/essentia:latest

# 1) Install required packages + python libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.9 python3.9-dev python3.9-distutils exiftool ffmpeg curl && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.9 && \
    python3.9 -m pip install --no-cache-dir \
        git+https://github.com/beetbox/beets.git \
        pyacoustid \
        requests \
        discogs-client \
        pylast \
        beets-xtractor \
        "beets[spotify]" \
        "beets[deezer]" \
        "beets[inline]" \
        "beets[discogs]" \
        "beets[info]" \
        "beets[fetchart]" \
        "beets[embedart]" \
        "beets[lastgenre]" \
        "beets[lyrics]" \
        watchdog \
        beautifulsoup4 \
        langdetect && \
    apt-get remove -y python3-pip && \
    rm -rf /var/lib/apt/lists/* /root/.cache/pip

# 2) Create a folder for our custom plugins and scripts
WORKDIR /app
RUN mkdir -p /app/plugins

# 3) Copy custom plugin + watch script if you want
COPY watch.py /app/watch.py
COPY config/plugins/comment.py /app/plugins/comment.py
COPY config/plugins/chroma.py /app/plugins/chroma.py
COPY config/plugins/spotify.py /app/plugins/spotify.py

# 4) By default, do nothing (or run a sleep).
CMD ["python3.9", "/app/watch.py"]
