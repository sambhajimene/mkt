# -------------------------------
# Base Image (stable + compatible)
# -------------------------------
    FROM python:3.10-slim

    # -------------------------------
    # Environment settings
    # -------------------------------
    ENV PYTHONDONTWRITEBYTECODE=1
    ENV PYTHONUNBUFFERED=1
    
    # -------------------------------
    # System dependencies
    # -------------------------------
    RUN apt-get update && apt-get install -y \
        curl \
        ca-certificates \
        build-essential \
        && rm -rf /var/lib/apt/lists/*
    
    # -------------------------------
    # Work directory
    # -------------------------------
    WORKDIR /app
    
    # -------------------------------
    # Copy requirements first (cache)
    # -------------------------------
    COPY requirements.txt .
    
    RUN pip install --no-cache-dir --upgrade pip \
        && pip install --no-cache-dir -r requirements.txt
    
    # -------------------------------
    # Copy project files
    # -------------------------------
    COPY . .
    
    # -------------------------------
    # Streamlit port
    # -------------------------------
    EXPOSE 5009
    
    # -------------------------------
    # Run Streamlit
    # -------------------------------
    CMD ["streamlit", "run", "main.py", "--server.port=5009", "--server.address=0.0.0.0"]
    