FROM ubuntu:22.04
RUN apt-get update && apt-get install -y python3 python3-pip git curl sudo wget nmap && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip3 install requests python-dotenv
CMD ["python3", "main.py"]