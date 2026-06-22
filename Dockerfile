# Stage 1: Build/Deps
FROM python:3.11-slim AS build
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app

RUN useradd --create-home appuser
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy installed packages from build stage
COPY --from=build /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

# Ensure .local/bin is in PATH
ENV PATH=/home/appuser/.local/bin:$PATH
USER appuser

EXPOSE 8007
# Start using uvicorn as a module to handle the 'src' package correctly
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8007"]
