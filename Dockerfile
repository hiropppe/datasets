FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /root

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential pkg-config locales tzdata \
    python3 python3-dev python3-pip python3-wheel python3-venv pipx \
    nodejs npm \
    file \
    vim git curl jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pipx ensurepath

RUN locale-gen ja_JP.UTF-8

ENV LANG ja_JP.UTF-8
ENV TZ Asia/Tokyo
ENV PATH="${PATH}:/root/.local/bin"

RUN ln -sf /usr/bin/python3.10 /usr/bin/python3
RUN ln -s /usr/bin/python3 /usr/bin/python

RUN npm install n -g
RUN n stable
RUN apt-get purge -y nodejs npm

RUN git clone --depth 1 https://github.com/taku910/mecab && \
    cd mecab/mecab && \
    ./configure --enable-utf8-only && \
    make && \
    make check && \
    make install && \
    #pip install --no-cache-dir mecab-python3==0.996.5 && \
    pip install --no-cache-dir mecab-python3 && \
    ldconfig && \
    cd ../mecab-ipadic && \
    ./configure --with-charset=utf8 && \
    make && \
    make install

RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git \
    && cd mecab-ipadic-neologd \
    && ./bin/install-mecab-ipadic-neologd -n -a -y

RUN pipx install poetry

COPY . /datasets

WORKDIR /datasets
RUN poetry install

CMD ["bash"]

