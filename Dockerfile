# ----------------------------
# Step 1: Base image
# ----------------------------
    FROM python:3.10-slim

    # ----------------------------
    # Step 2: Set working directory
    # ----------------------------
    WORKDIR /app
    
    # ----------------------------
    # Step 3: Copy requirements and install
    # ----------------------------
    COPY requirements.txt .
    RUN pip install --no-cache-dir --upgrade pip \
        && pip install --no-cache-dir -r requirements.txt
    
    # ----------------------------
    # Step 4: Copy Python code
    # ----------------------------
    COPY pro_option_alert_200symbols.py .
    
    # ----------------------------
    # Step 5: Set environment variables
    # ----------------------------
    ENV STREAMLIT_SERVER_PORT=5009
    ENV STREAMLIT_SERVER_HEADLESS=true
    ENV STREAMLIT_SERVER_ENABLECORS=false
    ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
    
    # Email secrets (use OpenShift secret in Deployment)
    # ENV EMAIL_FROM=your_email@gmail.com
    # ENV EMAIL_PASS=your_app_password
    # ENV EMAIL_TO=receiver_email@gmail.com
    
    # ----------------------------
    # Step 6: Expose port
    # ----------------------------
    EXPOSE 5009
    
    # ----------------------------
    # Step 7: Run Streamlit
    # ----------------------------
    CMD ["streamlit", "run", "pro_option_alert_200symbols.py", "--server.port", "5009"]
    