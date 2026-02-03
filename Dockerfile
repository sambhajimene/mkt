# Use official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script
COPY pro_option_alert_200symbols.py .

# Expose port for Flask dashboard
EXPOSE 5009

# Run your Python script
CMD ["python", "pro_option_alert_200symbols.py"]
