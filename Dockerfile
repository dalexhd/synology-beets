# Step 1: Use the pre-built Essentia image as the base
FROM mtgupf/essentia:latest

# Step 2: Install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Step 3: Install beets + relevant plugins
RUN pip3 install --no-cache-dir \
    beets \
    beets-xtractor \
    beets-spotify \
    beets-discogs \
    watchdog

# Step 4: Set up the working directory
WORKDIR /app

# Step 5: Copy your watch script (optional)
COPY watch.py /app/watch.py

# Step 6: Default command to run the watch script
CMD ["python3", "/app/watch.py"]
