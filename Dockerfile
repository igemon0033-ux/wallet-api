FROM python:3.11-slim

WORKDIR /workspace

# Install postgresql-client for pg_isready check
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies list
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure entrypoint is executable
RUN chmod +x entrypoint.sh

# Run entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
