FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/pyproject.toml ./backend/pyproject.toml
RUN python -m pip install --upgrade pip \
    && python -c "import subprocess, tomllib; project = tomllib.load(open('backend/pyproject.toml', 'rb'))['project']; subprocess.check_call(['python', '-m', 'pip', 'install', '--no-cache-dir', *project['dependencies']])"

COPY backend ./backend

EXPOSE 80

CMD ["sh", "-c", "exec uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-80}"]
