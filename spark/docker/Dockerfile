FROM bitnami/spark:3.5.5-debian-12-r7

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-numpy && \
    pip3 install --no-cache-dir pandas && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYSPARK_PYTHON=python3 \
    PYSPARK_DRIVER_PYTHON=python3

USER 1001