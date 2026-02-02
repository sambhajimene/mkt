# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy code and requirements
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 5010

# Run the script
CMD ["python", "pro_option_alert_200symbols.py"]

