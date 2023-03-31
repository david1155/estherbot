# Build stage
FROM python:alpine3.11

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install build tools
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev


# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clean up build tools
RUN apk del .build-deps

RUN apk add --no-cache libstdc++

# Copy the content of the local src directory to the working directory
COPY app.py /app
COPY templates /app/templates

# By default, listen on port 5000
EXPOSE 5000/tcp

# Set the working directory in the container
WORKDIR /app

# Specify the command to run on container start
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
