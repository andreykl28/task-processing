FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
COPY pyproject.toml ./pyproject.toml
COPY README.md ./README.md
COPY src ./src
COPY tests ./tests
COPY demo_tasks.json ./demo_tasks.json
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir .

CMD ["python3", "-m", "task_processing"]
