# 1. 파이썬 3.13 기반 이미지 사용
FROM python:3.13-slim

# 2. 컨테이너 내부 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (필요 시)
RUN apt-get update && apt-get install -y gcc

# 3. 필요한 라이브러리 설치를 위한 환경 설정
# .pyc 파일을 생성하지 않도록 설정
ENV PYTHONDONTWRITEBYTECODE=-1
# 로그가 실시간으로 출력되도록 설정
ENV PYTHONUNBUFFERED=1

# 4. 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 현재 디렉토리의 모든 파일을 컨테이너의 /app으로 복사
COPY . .

# 6. FastAPI 실행 (8000 포트)
EXPOSE 8000

# 7. 서버 실행 명령어
# 호스트를 0.0.0.0으로 설정해야 외부(EC2 등)에서 접속이 가능합니다.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]