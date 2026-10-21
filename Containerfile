# The deploy workflow builds this after `make container-context`, which puts the
# app's wheel in dist/ and its locked dependencies, with hashes, in
# requirements.txt. The app runs as an unprivileged user on a read-only
# filesystem; it may write only to /data (and /tmp).
FROM docker.io/library/python:3.13-slim

RUN useradd --system --uid 10001 --no-create-home app \
    && mkdir /data && chown app /data
WORKDIR /app
COPY requirements.txt dist/*.whl ./
RUN pip install --no-cache-dir --require-hashes -r requirements.txt \
    && pip install --no-cache-dir --no-deps ./*.whl \
    && rm -f requirements.txt ./*.whl

USER 10001
# TODO_DB_PATH keeps the task database in the writable /data volume.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000 DATA_DIR=/data \
    TODO_DB_PATH=/data/todo.db
EXPOSE 8000
# 0.0.0.0 inside the container only. The server publishes the port on
# 127.0.0.1, with no reverse proxy, so only the server itself reaches it (ADR 0007).
CMD ["sh", "-c", "exec uvicorn kickoff_trial.main:create_app --factory --host 0.0.0.0 --port \"$PORT\""]
