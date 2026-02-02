# # =====================
# # Use official Python image
# # =====================
# FROM python:3.12-slim

# # Set working directory
# WORKDIR /app

# # Copy application code
# COPY . /app

# # Install dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Expose Flask port
# EXPOSE 5009

# # Run Flask app on 0.0.0.0:5009
# CMD ["python", "pro_option_alert_200symbols.py"]

FROM python:3.12-slim

WORKDIR /app

# system deps (ta + pandas safe)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pro_option_alert_200symbols.py .

EXPOSE 5000

CMD ["python", "pro_option_alert_200symbols.py"]
