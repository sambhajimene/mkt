# =====================
# Use official Python image
# =====================
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy application code
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 5009

# Run Flask app on 0.0.0.0:5009
CMD ["python", "pro_option_alert_200symbols.py"]
