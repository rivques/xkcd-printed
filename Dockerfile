FROM python:3.11-slim

# Install system deps needed by some Python packages (OpenCV, Pillow, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libglib2.0-0 \
       libsm6 \
       libxext6 \
       libxrender1 \
       libgl1 \
       ca-certificates \
       dbus \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project
COPY . /app

# Install Python dependencies from pyproject
RUN pip install --no-cache-dir pip setuptools wheel \
    && pip install --no-cache-dir "bleak==0.22.3" "numpy==2.2.4" "opencv-python==4.11.0.86" "pillow>=12.0.0" "python-dotenv>=1.2.1" "xkcd>=2.4.2"

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "xckd_forever.py"]
