# Use Debian Bullseye as our base
FROM debian:bullseye

# 1. Install system/build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    cmake \
    libsamplerate0-dev \
    libfftw3-dev \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Clone and build Essentia from source (with xtractor)
RUN git clone --depth 1 https://github.com/MTG/essentia.git /essentia
WORKDIR /essentia

# Create a build directory and compile
RUN mkdir build && cd build && \
    cmake -DCMAKE_BUILD_TYPE=Release \
          -DBUILD_EXAMPLES=ON \
          -DBUILD_TESTS=OFF \
          .. && \
    make -j"$(nproc)" && \
    make install && \
    ldconfig

# 3. Return to a working directory for the app
WORKDIR /app

# 4. Install beets + relevant plugins
#    (beets-xtractor plugin will call the 'xtractor' binary we just built)
RUN pip3 install --no-cache-dir \
    beets \
    beets-xtractor \
    beets-spotify \
    beets-discogs \
    watchdog

# 5. Copy your watch script (optional)
COPY watch.py /app/watch.py

# 6. Default command to run the watch script
CMD ["python3", "/app/watch.py"]
