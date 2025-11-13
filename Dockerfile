FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps (if any) and install requirements
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 5000

CMD ["gunicorn", "wsgi:application", "-b", "0.0.0.0:5000", "-w", "3"]
