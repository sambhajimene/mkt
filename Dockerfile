## Use official Python 3.10 image with slim variant
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install build tools and dependencies for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY . .

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=5009

# Expose Streamlit port
EXPOSE 5009

# Run Streamlit
CMD ["streamlit", "run", "main.py", "--server.port", "5009", "--server.address", "0.0.0.0"]
