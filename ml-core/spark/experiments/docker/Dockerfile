FROM ubuntu:16.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        default-jdk \
        wget \
        python \
        software-properties-common \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py && \
    rm get-pip.py

RUN pip --no-cache-dir install \
        ipykernel \
        jupyter \
        && \
    python -m ipykernel.kernelspec

RUN pip --no-cache-dir install \
    pyspark==2.3.2

RUN pip --no-cache-dir install \
        toree \
        && \
    jupyter toree install --spark_home=/usr/local/lib/python2.7/dist-packages/pyspark

WORKDIR /notebooks
ENV SPARK_HOME /usr/local/lib/python2.7/dist-packages/pyspark

CMD ["jupyter", "notebook", "--KernelSpecManager.ensure_native_kernel=False"]
