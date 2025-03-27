# Step 1: Use the pre-built Essentia image as the base
FROM mtgupf/essentia:latest

# Step 2: Install necessary packages and Python plugins
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev ffmpeg && \
    pip3 install --no-cache-dir \
        beets \
        beets-xtractor \
        "beets[spotify]" \
        "beets[discogs]" \
        watchdog && \
    rm -rf /var/lib/apt/lists/* /root/.cache/pip

# Step 3: Set up the working directory
WORKDIR /app

# Step 4: Copy your watch script
COPY watch.py /app/watch.py

# Step 5: Default command to run the watch script
CMD ["python3", "/app/watch.py"]
