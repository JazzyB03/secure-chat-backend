#lightweight Python runtime version
FROM python:3.11-slim

#setting the working directory inside the container
WORKDIR /app

#Stop python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

#Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copy the rest of the source code
COPY ./src ./src

#Expose the port FastAPI will run on
EXPOSE 8000

#Command to run the application using Uvicorn
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]