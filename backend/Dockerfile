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
# Run uvicorn server (Shell form is more stable on some platforms)
# Run uvicorn server (Shell form is more stable on some platforms)
# We use || sleep 3600 to catch startup errors (Keep-Alive for debugging)
# Standard Production Command
# Using python -m uvicorn is generally safer for path resolution
# Run using direct python script to ensure our print statements fire BEFORE uvicorn starts
# Also keep the sleep trap to prevent crash loop
CMD ["sh", "-c", "python main.py || (echo '❌ APP CRASHED' && sleep 3600)"]
