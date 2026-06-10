# myRoomie web build: one FastAPI container serving the API, the static web
# client (web/), and the portrait assets. Played in a browser at the mapped port.
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir "fastapi>=0.110" "uvicorn[standard]>=0.27" "pydantic>=2.6"

COPY server/ server/
COPY web/ web/
COPY client/assets/ client/assets/

RUN mkdir -p /data
ENV PYTHONPATH=/app/server

EXPOSE 8060
CMD ["python", "-m", "myroomie", "--host", "0.0.0.0", "--port", "8060", "--db", "/data/myroomie.db"]
