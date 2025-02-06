FROM python:alpine3.21

ENV PYTHONUNBUFFERED=true

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
ENV SM2_VERSION=0.1.3
COPY . /app
WORKDIR /app
ENTRYPOINT ["python3"]
HEALTHCHECK --interval=5s --timeout=1s --start-period=5s --retries=1 CMD ps aux | grep 'gunicorn' || exit 1
CMD ["/usr/local/bin/gunicorn","-w", "1","-t", "1", "-b","0.0.0.0:8456","--timeout","5","app:app"]