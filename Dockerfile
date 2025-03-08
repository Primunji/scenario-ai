FROM python:3.9-slim

# 2. 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && apt-get clean

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 복사
COPY requirements.txt .

# 5. 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 6. 애플리케이션 소스 복사
COPY . .

# 7. SSL 인증서 파일 경로를 환경 변수로 설정
ENV SSL_CERT_PATH=/certs/fullchain.pem
ENV SSL_KEY_PATH=/certs/privkey.pem

# 8. FastAPI 앱 실행 (SSL을 사용하여)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443", "--ssl-keyfile", "/certs/privkey.pem", "--ssl-certfile", "/certs/fullchain.pem"]
