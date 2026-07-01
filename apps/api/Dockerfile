FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["uv", "run", "uvicorn", "researchos_api.main:app", "--host", "0.0.0.0", "--app-dir", "src"]
