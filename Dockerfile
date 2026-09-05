# Use lightweight official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000
ENV HOST=0.0.0.0

# Copy application files
COPY app.py .
COPY german_daily_roots_top1000.json .
COPY already_memorized_words.json .
COPY README.md .

# Expose port (Render sets $PORT dynamically)
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
