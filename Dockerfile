FROM python:3.12-slim AS base
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential gcc ca-certificates && rm -rf /var/lib/apt/lists/*

FROM base AS builder
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip
RUN pip wheel --no-deps --wheel-dir /app/wheels -r /app/requirements.txt

FROM base
COPY --from=builder /app/wheels /wheels
RUN pip install --no-index --find-links=/wheels -r /app/requirements.txt
COPY . /app
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
