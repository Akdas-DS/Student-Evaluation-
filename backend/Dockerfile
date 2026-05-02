FROM python:3.11-slim

WORKDIR /app

# Copy the requirements file from the current folder (backend)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory into the container
COPY . .

# Expose the port (Render sets the PORT environment variable)
EXPOSE 10000

# Start the FastAPI app using Uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
