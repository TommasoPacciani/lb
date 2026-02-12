FROM iwaseyusuke/mininet:latest

# Install testing tools and utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
        iperf \
        arping \
        tcpdump \
        tshark \
        curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app/

# Make scripts executable
RUN chmod +x run_tests.sh entrypoint.sh

CMD ["bash"]
