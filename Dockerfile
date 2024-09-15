# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose Flask's default port
EXPOSE 5000

# Set environment variables to prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

# Run the Flask app
CMD ["python", "app.py"]
