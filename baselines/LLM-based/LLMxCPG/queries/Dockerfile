FROM alpine:3.19
RUN apk update && apk upgrade && apk add --no-cache \
    git \
    curl \
    wget \
    unzip \
    python3 \
    py3-pip \
    openjdk17-jdk \
    gnupg \
    bash \
    nss \
    ncurses \
    php
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir huggingface_hub
WORKDIR /app
RUN printf '%s\n' \
    'from huggingface_hub import hf_hub_download' \
    'repo_id = "QCRI/LLMxCPG-Code"' \
    'filename = "all_source_code.zip"' \
    'print(f"Attempting to download {filename} from {repo_id}...")' \
    'file_path = hf_hub_download(repo_id=repo_id, filename=filename, repo_type="dataset", local_dir="/app")' \
    'print(f"Successfully downloaded to {file_path}")' > download_dataset.py
RUN python download_dataset.py
RUN mkdir joern && cd joern \
    && curl -L "https://github.com/joernio/joern/releases/latest/download/joern-install.sh" -o joern-install.sh \
    && chmod u+x joern-install.sh \
    && bash ./joern-install.sh --without-plugins
RUN mkdir -p /opt/joern/joern-cli && \
    unzip -j /app/all_source_code.zip -d /opt/joern/joern-cli
EXPOSE 9685
WORKDIR /opt/joern/joern-cli

CMD ["./joern", "--server", "--server-host", "0.0.0.0", "--server-port", "9685"]