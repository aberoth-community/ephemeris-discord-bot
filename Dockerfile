# Use an official Python runtime as a parent image
FROM python:3.10

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel build

# Build the wheel
RUN python -m build --wheel --no-isolation

# Install the wheel
RUN pip install --no-cache-dir dist/*.whl

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["python", "-m", "ephemeris"]
