FROM python:3.10 as Builder
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install --upgrade pip
WORKDIR /app
RUN apt-get update && apt-get install libgl1 -y
RUN git clone https://github.com/OpenBMB/BMTools.git --depth=1
RUN cd BMTools && \
    pip install -r requirements.txt && \
    python setup.py develop
WORKDIR /app/AgentVerse
COPY requirements*.txt ./
RUN pip install -r requirements.txt
RUN pip install -r requirements_local.txt
COPY . .
RUN pip install -e .
