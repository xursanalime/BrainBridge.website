FROM python:3.11-slim

WORKDIR /app

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything
COPY . .

# Set working directory to backend
WORKDIR /app/backend

# Run the app using python so it picks up os.getenv('PORT') safely
CMD ["python", "main.py"]
