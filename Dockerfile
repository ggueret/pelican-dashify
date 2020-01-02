FROM ggueret/multipy:latest
ENV DEBIAN_FRONTEND noninteractive

ENV MP4BOX_VERSION 0.7.1
RUN apt-get update && apt-get install -y build-essential curl make && \
	mkdir /tmp/mp4box && cd /tmp/mp4box/ && \
	curl -sL https://github.com/gpac/gpac/archive/v$MP4BOX_VERSION.tar.gz > gpac-$MP4BOX_VERSION.tar.gz && \
	tar xf gpac-$MP4BOX_VERSION.tar.gz && cd gpac-0.7.1/ && \
	./configure --static-mp4box --use-zlib=no && make -j$(nproc) && make install && \
	cd / && rm -rf /tmp/mp4box/ && \
	apt-get remove -y curl build-essential build-essential curl make && \
	apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

ENV FFMPEG_41_VERSION 4.1.3
RUN apt-get update && apt-get install -y curl build-essential make nasm libx264-155 libx264-dev yasm && \
	mkdir /tmp/ffmpeg && cd /tmp/ffmpeg/ && \
	curl -sL http://ffmpeg.org/releases/ffmpeg-$FFMPEG_41_VERSION.tar.gz > ffmpeg-$FFMPEG_41_VERSION.tar.gz && \
	tar xf ffmpeg-$FFMPEG_41_VERSION.tar.gz && cd ffmpeg-$FFMPEG_41_VERSION/ && \
	./configure --enable-gpl --enable-libx264 && \
	make -j$(nproc) && make install && \
	cd / && rm -rf /tmp/ffmpeg/ && \
	apt-get remove -y curl build-essential make nasm libx264-dev yasm && \
	apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# make Python 3.6 as default version
RUN ln -sf /usr/local/bin/python3.6 /usr/local/bin/python && ln -sf /usr/local/bin/pip3.6 /usr/local/bin/pip

#ADD . /usr/src/app
WORKDIR /usr/src/app

RUN pip install --upgrade pip && pip install tox
CMD ["tox"]
