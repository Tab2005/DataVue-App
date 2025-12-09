# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 8000
EXPOSE 8000

# Run uvicorn server
# Run uvicorn server using python -m to ensure path resolution
# Run uvicorn server using shell to trap errors and keep container alive for debugging
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port 8000 || (echo '❌ APP CRASHED! Keeping container alive for debug...' && sleep 3600)"]
