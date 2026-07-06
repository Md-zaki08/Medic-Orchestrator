FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .

ENV GEMINI_API_KEY=""
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["streamlit", "run", "src/app/ui.py", "--server.port=8080", "--server.enableCORS=false"]
