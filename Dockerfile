# Use Alpine base image for smaller size
FROM python:3.11-alpine AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# First stage creates a virtual environment and installs packages.
FROM base AS build

# Install necessary packages for building
RUN apk update \
 && apk add --no-cache git gcc\
 && python -m venv /venv \
 && /venv/bin/pip install --upgrade pip

# Copy and install requirements
COPY requirements.txt ./
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# Final stage is the image you'll actually run
FROM base
COPY --from=build /venv/ /venv/
ENV PATH=/venv/bin:$PATH

COPY ./ ./
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
