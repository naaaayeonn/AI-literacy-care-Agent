FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# FastAPI 포트 노출
EXPOSE 8000

# run.py 진입점 실행
CMD ["python", "run.py"]
