# ============================================================
# Stage 1: base — shared by dev and prod
# ============================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg gosu && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.docker.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Fonts layer (168 MB, rarely changes — maximizes layer caching)
COPY fonts/ fonts/

# Application code
COPY templates/ templates/
COPY static/ static/
COPY plugins/ plugins/
COPY .env.example .env.example
COPY icon.png icon.ico ./
COPY app.py launcher.py path_utils.py patreon.py ffmpeg_renderer.py ./

RUN mkdir -p output

ENV FLASK_HOST=0.0.0.0 \
    PORT=8787

EXPOSE 8787

# ============================================================
# Stage 2: prod — optimized production image
# ============================================================
FROM base AS prod

RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser && \
    chown -R appuser:appuser /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8787/health')" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "launcher.py", "--headless"]

# ============================================================
# Stage 3: dev — development with hot reload
# ============================================================
FROM base AS dev

ENV FLASK_DEBUG=1 \
    PORT=5000

EXPOSE 5000

CMD ["python", "app.py"]
