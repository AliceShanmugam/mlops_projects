# Base image
FROM prefecthq/prefect@sha256:c290bae3b8dc237bcdeeb7ee22ef80d5d75a66eaf9f770afca572d1294854f4d as base

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    iputils-ping \
    net-tools \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Development image
FROM base as development

# Install development tools and Docker CLI
RUN apt-get update && apt-get install -y \
    vim \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Add Docker group and permissions
RUN groupadd -g 999 docker || true && \
    usermod -aG docker root

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Working directory
WORKDIR /workspace

# Production image
FROM base as production

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Working directory
WORKDIR /workspace

# Create necessary directories
RUN mkdir -p /workspace/data /workspace/flows /workspace/mlruns
