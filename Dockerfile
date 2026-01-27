# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml pyproject.toml
COPY src/ src/
COPY main.py main.py

# Install dependencies using uv
RUN uv venv /app/.venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN uv pip install -e .

# Create directory for credentials and database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/meals.db
ENV GOOGLE_CREDENTIALS_PATH=/app/data/credentials.json

# Expose webhook port (if used)
EXPOSE 8080

# Run the bot
CMD ["python", "main.py"]
