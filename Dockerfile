FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install aiohttp

# RUN pip install pynacl

RUN apt-get update && apt-get install -y libsodium23 && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

EXPOSE 5000

CMD [ "python", "app.py" ]