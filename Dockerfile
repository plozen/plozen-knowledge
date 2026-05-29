FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir .

EXPOSE 8100

CMD ["uvicorn", "plozen_knowledge_api.main:app", "--host", "0.0.0.0", "--port", "8100"]
