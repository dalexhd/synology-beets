# ----------------------------------------------------------------------------
# Beets + custom plugins image
# Based on mtgupf/essentia, extended with build tools and Beets extras
# ----------------------------------------------------------------------------

FROM mtgupf/essentia:latest

# ---------------------------------------------------------------------------
# 1. System dependencies
#    * build-essential + Meson/Ninja: compile PyGObject & pycairo once
#    * GI/Cairo headers: runtime for replaygain & bpd extras
#    * Utility binaries: ffmpeg, exiftool, curl, git
#    * Python 3.9 tool‑chain (matching upstream image)
# ---------------------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc g++ \
        pkg-config meson ninja-build \
        libcairo2-dev libgirepository1.0-dev python3-gi \
        python3.9 python3.9-dev python3.9-distutils \
        exiftool ffmpeg curl git && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# 2. Python tooling – install pip & wheel first
# ---------------------------------------------------------------------------
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.9 && \
    python3.9 -m pip install --no-cache-dir --upgrade pip wheel

    # ---- Python bootstrap ----
RUN python3.9 -m pip install --no-cache-dir --upgrade \
    pip setuptools wheel "packaging>=24.0"

# ---------------------------------------------------------------------------
# 3. Python libraries – core + Beets with extras
#    * spotify extra removed (deprecated)
#    * replaygain kept – uses GI deps provided above
# ---------------------------------------------------------------------------
RUN python3.9 -m pip install --no-cache-dir \
        git+https://github.com/beetbox/beets.git \
        python-dotenv \
        pyacoustid \
        requests \
        discogs-client \
        pylast \
        flask \
        pillow \
        beets-xtractor \
        beets-beatport4 \
        "beets[deezer]" \
        "beets[inline]" \
        "beets[discogs]" \
        "beets[fetchart]" \
        "beets[embedart]" \
        "beets[lastgenre]" \
        "beets[lyrics]" \
        "beets[replaygain]" \
        watchdog \
        beautifulsoup4 \
        langdetect && \
    rm -rf /root/.cache/pip

# ---------------------------------------------------------------------------
# 4. Application layout
# ---------------------------------------------------------------------------
WORKDIR /app
ENV PLUGINS_PATH=/app/plugins \
    SCRIPTS_PATH=/app/scripts

RUN mkdir -p \
    $PLUGINS_PATH \
    $SCRIPTS_PATH \
    /app/logs /app/data /app/config

# ---------------------------------------------------------------------------
# 5. Copy custom plugins & scripts
# ---------------------------------------------------------------------------
COPY src/plugins/*.py $PLUGINS_PATH/
COPY src/scripts/watch.py $SCRIPTS_PATH/

# ---------------------------------------------------------------------------
# 6. Default command
# ---------------------------------------------------------------------------
CMD ["sh", "-c", "python3.9 $SCRIPTS_PATH/watch.py"]
