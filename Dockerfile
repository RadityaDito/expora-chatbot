# Use official Python image as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy only requirements first (to improve Docker build caching)
COPY requirements.txt /app/requirements.txt

# Install dependencies separately before copying the rest of the app
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . /app

# Expose port 8000
EXPOSE 8000

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
