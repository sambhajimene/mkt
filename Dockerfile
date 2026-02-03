FROM python:3.11-slim

WORKDIR /app

# System deps (important for pandas-ta)
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY pro_option_alert_200symbols.py .

EXPOSE 5009

CMD ["python", "pro_option_alert_200symbols.py"]
