# Use Python 3.12 as the runtime environment
FROM python:3.12-slim

# Copy uv from the official uv image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the application working directory
WORKDIR /app

# Copy dependency files first to improve Docker layer caching
COPY pyproject.toml uv.lock README.md ./

# Install project dependencies from the lock file
RUN uv sync --frozen --no-install-project

# Copy the application source code
COPY src ./src

# Install the project itself
RUN uv sync --frozen

# Expose the FastAPI port
EXPOSE 8000

# Start the FastAPI application
CMD ["uv", "run", "uvicorn", "day03_python_engineering.api.app:app", "--host", "0.0.0.0", "--port", "8000"]