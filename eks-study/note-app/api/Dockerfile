FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ARG VERSION=v1
ENV VERSION=${VERSION} DATA_DIR=/tmp LOG_LEVEL=INFO
EXPOSE 8080
CMD ["python", "app.py"]
