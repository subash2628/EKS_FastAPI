# --- build stage ---
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# --- final stage ---
FROM python:3.12-slim

# non-root user
RUN useradd --no-create-home --shell /bin/false appuser

WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .

USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
