# GPTL governed-capture firewall DEMO service (not the packaged library).
# Two stages: build the React SPA, then a Python image that serves the FastAPI
# API + the built SPA together under /gptl. Build context = gptl repo root.

# ── stage 1: build the SPA ──────────────────────────────────────────────────
FROM node:22-slim AS web
WORKDIR /web
COPY demo/web/package.json demo/web/package-lock.json ./
# npm install (not ci) so linux-only native deps (@tailwindcss/oxide, @emnapi)
# resolve correctly from a lockfile generated on another platform.
RUN npm install --no-audit --no-fund --loglevel=error
COPY demo/web/ ./
# Absolute base + API path so assets and calls resolve behind the /gptl proxy.
ENV VITE_BASE=/gptl/
ENV VITE_API_BASE=/gptl/api
RUN npm run build          # -> /web/dist

# ── stage 2: python runtime ─────────────────────────────────────────────────
FROM python:3.12-slim
WORKDIR /app

# Install the governed engine (boundstate-gptl) from source, then the demo deps.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY demo/requirements.txt ./demo-requirements.txt
RUN pip install --no-cache-dir -r demo-requirements.txt

# App code + the built SPA (app.py serves ../web/dist relative to backend/).
COPY demo/backend ./backend
COPY --from=web /web/dist ./web/dist

ENV HOST=0.0.0.0
ENV PORT=8080
ENV PUBLIC_BASE_PATH=/gptl
EXPOSE 8080
CMD ["sh", "-c", "uvicorn --app-dir backend app:app --host ${HOST:-0.0.0.0} --port ${PORT:-8080}"]
