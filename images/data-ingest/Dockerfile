# images/data-ingest/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# install required packages
RUN pip install --no-cache-dir \
    mysql-connector-python \
    pandas \
    python-dotenv

# copy the script
COPY ingest.py .

# make script executable
RUN chmod +x ingest.py

# command to run the script
CMD ["python", "ingest.py"]