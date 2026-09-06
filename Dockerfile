# Use lightweight official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000
ENV HOST=0.0.0.0

# Copy all application files, datasets (.json), and reference PDFs (.pdf)
COPY . .

# Expose port (Render sets $PORT dynamically)
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
