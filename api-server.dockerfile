FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install the required packages
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-pip \
    portaudio19-dev \
    libpq-dev

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY ./src /app/src

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Use the start script as the entrypoint
CMD ["python3", "-m", "src.Search"]
