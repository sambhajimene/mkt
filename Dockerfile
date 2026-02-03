FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script
COPY pro_option_alert_200symbols.py .

# Expose port for Flask dashboard
EXPOSE 5009

# Run the script
CMD ["python", "pro_option_alert_200symbols.py"]
