FROM ggueret/multipy:latest
ENV DEBIAN_FRONTEND noninteractive

ARG MP4BOX_VERSION="0.7.1"
ARG MP4BOX_PACKAGES="zlib1g"
ARG MP4BOX_BUILD_PACKAGES="build-essential curl make pkg-config zlib1g-dev"

ARG FFMPEG_41_VERSION="4.1.3"
ARG FFMPEG_PACKAGES="libx264-155"
ARG FFMPEG_BUILD_PACKAGES="curl build-essential make nasm libx264-dev yasm"

# Install MP4Box
RUN apt-get update && apt-get -y install --no-install-recommends ${MP4BOX_BUILD_PACKAGES} ${MP4BOX_PACKAGES} && \
	mkdir /tmp/mp4box && cd /tmp/mp4box/ && \
	curl -sL https://github.com/gpac/gpac/archive/v${MP4BOX_VERSION}.tar.gz > gpac-${MP4BOX_VERSION}.tar.gz && \
	tar xf gpac-${MP4BOX_VERSION}.tar.gz && cd gpac-0.7.1/ && \
	./configure --static-mp4box --use-zlib=no && make -j$(nproc) && make install && \
	cd / && rm -rf /tmp/mp4box/ && apt-get remove -y ${MP4BOX_BUILD_PACKAGES} && rm -rf /var/lib/apt/lists/*

# Install ffmpeg
RUN apt-get update && apt-get -y install --no-install-recommends ${FFMPEG_BUILD_PACKAGES} ${FFMPEG_PACKAGES} && \
	mkdir /tmp/ffmpeg && cd /tmp/ffmpeg/ && \
	curl -sL http://ffmpeg.org/releases/ffmpeg-${FFMPEG_41_VERSION}.tar.gz > ffmpeg-${FFMPEG_41_VERSION}.tar.gz && \
	tar xf ffmpeg-${FFMPEG_41_VERSION}.tar.gz && cd ffmpeg-${FFMPEG_41_VERSION}/ && \
	./configure --enable-gpl --enable-libx264 && make -j$(nproc) && make install && \
	cd / && rm -rf /tmp/ffmpeg/ && apt-get remove -y ${FFMPEG_BUILD_PACKAGES} && rm -rf /var/lib/apt/lists/*

# make Python 3.8 as default version
RUN ln -sf /usr/local/bin/python3.8 /usr/local/bin/python && ln -sf /usr/local/bin/pip3.8 /usr/local/bin/pip

# Install test packages
RUN apt-get update && apt-get -y install --no-install-recommends \
	gstreamer1.0-tools gstreamer1.0-plugins-base && \
	rm -rf /var/lib/apt/lists/*

COPY . /usr/src/app
WORKDIR /usr/src/app

RUN pip install --upgrade pip && pip install tox
RUN pip install -e ".[testing]"
CMD ["tox"]
