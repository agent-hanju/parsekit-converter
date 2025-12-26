FROM python:3.12-slim

# Install LibreOffice with H2Orestart extension for HWP support
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    libreoffice \
    libreoffice-java-common \
    fonts-unfonts-core \
    wget \
    && wget -q -O /tmp/H2Orestart.oxt \
        "https://github.com/ebandal/H2Orestart/releases/download/v0.7.9/H2Orestart.oxt" \
    && unopkg add --shared /tmp/H2Orestart.oxt \
    && rm /tmp/H2Orestart.oxt \
    && apt-get purge -y wget \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
