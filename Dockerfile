# ----------------------------------------------------------------------------
# Beets + custom plugins image
# ----------------------------------------------------------------------------
FROM debian:bullseye

# ----------------------------------------------------------------------------
# 1. System dependencies
# ----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ pkg-config meson ninja-build \
    libcairo2-dev libgirepository1.0-dev python3-gi \
    python3.9 python3.9-dev python3.9-distutils \
    exiftool ffmpeg curl git cmake \
    libsamplerate0-dev libfftw3-dev \
    libavcodec-dev libavformat-dev libavutil-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*


# ----------------------------------------------------------------------------
# 2. Python tooling – install pip & wheel
# ----------------------------------------------------------------------------
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.9 && \
    python3.9 -m pip install --no-cache-dir --upgrade \
    pip setuptools wheel packaging>=24.0

# ----------------------------------------------------------------------------
# 3. Python libraries – core + Beets with extras
# ----------------------------------------------------------------------------
RUN python3.9 -m pip install --no-cache-dir \
    git+https://github.com/beetbox/beets.git \
    python-dotenv pyacoustid requests discogs-client pylast pillow \
    beets-xtractor beets-beatport4 \
    "beets[deezer]" "beets[inline]" "beets[discogs]" "beets[mbsync]" \
    "beets[fetchart]" "beets[embedart]" "beets[lastgenre]" \
    "beets[lyrics]" "beets[replaygain]" \
    watchdog beautifulsoup4 langdetect \
    && rm -rf /root/.cache/pip

# ----------------------------------------------------------------------------
# 4. Application layout
# ----------------------------------------------------------------------------
WORKDIR /app
ENV PLUGINS_PATH=/app/plugins \
    SCRIPTS_PATH=/app/scripts

RUN mkdir -p $PLUGINS_PATH $SCRIPTS_PATH /app/logs /app/data /app/config && \
    chmod -R 777 /app/logs /app/data /app/config

# ----------------------------------------------------------------------------
# 5. Copy custom plugins & scripts
# ----------------------------------------------------------------------------
# COPY src/plugins/*.py $PLUGINS_PATH/
COPY src/scripts/watch.py $SCRIPTS_PATH/

# ----------------------------------------------------------------------------
# 6. Default command
# ----------------------------------------------------------------------------
CMD ["python3.9", "/app/scripts/watch.py"]