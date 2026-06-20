FROM debian:bookworm-slim

ARG WHISPER_CPP_REF=master

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        cmake \
        curl \
        ffmpeg \
        g++ \
        git \
        make \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch ${WHISPER_CPP_REF} https://github.com/ggml-org/whisper.cpp /opt/whisper.cpp \
    && cmake -S /opt/whisper.cpp -B /opt/whisper.cpp/build -DWHISPER_BUILD_SERVER=ON \
    && cmake --build /opt/whisper.cpp/build --config Release -j

COPY entrypoint.sh /usr/local/bin/invoxia-whisper-entrypoint
RUN chmod +x /usr/local/bin/invoxia-whisper-entrypoint

EXPOSE 9000
ENTRYPOINT ["invoxia-whisper-entrypoint"]
