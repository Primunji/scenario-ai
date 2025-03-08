FROM python:3.10

COPY . /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

WORKDIR /app

EXPOSE 443

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--ssl-keyfile", "/certs/key.pem", "--ssl-certfile", "/certs/cert.pem"]