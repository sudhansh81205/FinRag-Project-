# FinRAG Production Container for Hugging Face Spaces / Docker
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy source code and configurations
COPY src/ ./src/
COPY configs/ ./configs/
COPY pyproject.toml .

# Expose port for Gradio (Member 7 Frontend)
EXPOSE 7860

# Default command launches Gradio app
CMD ["python", "-m", "pytest", "-v"]
