FROM python:3.13-slim

WORKDIR /app

# Copy tất cả file của backend vào container
COPY . .

# Cài dependencies
RUN pip install --no-cache-dir -r api/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
