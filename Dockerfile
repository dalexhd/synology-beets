FROM debian:bullseye

# 1. Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git build-essential python3 python3-dev python3-pip ffmpeg \
      libessentia-dev essentia-examples \
      && rm -rf /var/lib/apt/lists/*

# 2. Install beets + plugins (xtractor, spotify, discogs, watchdog, etc.)
RUN pip3 install --no-cache-dir beets beets-xtractor beets-spotify beets-discogs watchdog

# 3. Create a working directory
WORKDIR /app

# 4. Copy the watch script
COPY watch.py /app/watch.py

# 5. Default command: run the watch script
CMD ["python3", "/app/watch.py"]
