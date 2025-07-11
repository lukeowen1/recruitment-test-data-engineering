# images/data-output/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# install required packages
RUN pip install --no-cache-dir \
    mysql-connector-python \
    python-dotenv

# copy the script
COPY output.py .

# make script executable
RUN chmod +x output.py

# command to run the script
CMD ["python", "output.py"]