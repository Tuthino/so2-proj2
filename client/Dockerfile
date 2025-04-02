FROM python:3.9-slim
WORKDIR /app
COPY . .

# Install ping and procps for Kill
# nc and ss as well
RUN apt-get update && apt-get install -y \
    procps \
    iputils-ping \
    netcat-openbsd \
    iproute2

# Make the run script executable
RUN chmod +x run.sh

# run.sh allows for hot-reload with:
# docker-compose exec  client kill -USR1 1
CMD ["./run.sh"]
