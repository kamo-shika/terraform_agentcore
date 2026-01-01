FROM python:3.14-slim

WORKDIR /var/task

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Set the CMD to your handler (could be different depending on how AgentCore invokes the container)
# For standard Lambda-like invocation:
CMD ["main.handler"]
