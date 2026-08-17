FROM python:3.14-slim

WORKDIR /app

# Install Python dependencies first so Docker can cache this layer.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the project into the container.
COPY . .

# Run the pipeline module by default.
CMD ["python", "-m", "src.main"]