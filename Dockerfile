# Use a slim Python image for a smaller footprint
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies if any (none strictly needed for this app, but good practice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Hugging Face Spaces requires the app to run as a non-root user with UID 1000
RUN useradd -m -u 1000 user
USER user

# Expose the port Hugging Face expects
EXPOSE 7860

# Start the application in web mode
CMD ["python", "main.py", "--web"]