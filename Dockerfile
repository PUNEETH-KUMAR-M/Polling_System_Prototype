# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt first to leverage Docker's caching ability
COPY requirements.txt /app/

# Install the dependencies from the requirements.txt
RUN apt-get update && apt-get install -y libpq-dev python3-dev gcc
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages



# Copy the rest of your application code to the container
COPY . /app/

# Expose the port the app will run on (Flask default is 5000)
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]
