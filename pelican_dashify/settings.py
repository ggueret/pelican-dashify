from __future__ import unicode_literals

import json

DEFAULT_CONFIG = {
    "DASHIFY_METATAG": "{dashify}",
    "DASHIFY_EXTRACT_TAGS": True,
    "DASHIFY_CACHE_PATH": None,

    # bitrate computed from 0.1bpp @ 24fps
    "DASHIFY_VIDEO_MAX_WIDTH": 7680,
    "DASHIFY_VIDEO_MAX_HEIGHT": 4320,
    "DASHIFY_VIDEO_MAX_BITRATE": 79626,

    "DASHIFY_VIDEO_MIN_WIDTH": 128,
    "DASHIFY_VIDEO_MIN_HEIGHT": 72,
    "DASHIFY_VIDEO_MIN_BITRATE": 22,

    "DASHIFY_RESOLUTION_DIVISOR": 2,
    "DASHIFY_SEGMENT_DURATION": 4,
    "DASHIFY_BITS_PER_PIXEL": 0.1,
    "DASHIFY_FRAMERATE": 24,
    "DASHIFY_X264_PRESET": "slow",
    "DASHIFY_DASH_PROFILE": "onDemand",

    "DASHIFY_VIDEO_REPRESENTATIONS": 3,
    "DASHIFY_VIDEO_STREAM_INDEX": 0,

    "DASHIFY_AUDIO_CODEC": "aac",
    "DASHIFY_AUDIO_CHANNELS": 2,
    "DASHIFY_AUDIO_BITRATE": 128,  # in kbps
    "DASHIFY_AUDIO_DISABLE": False,
    "DASHIFY_AUDIO_STREAM_INDEX": 0,

    "DASHIFY_INFO_COMMAND": "{ffprobe} -v quiet -print_format json -show_format -show_streams -sexagesimal {input}",
    "DASHIFY_SEXAGESIMAL_REGEX": r"(?P<hours>\d+):(?P<minutes>\d+)+:(?P<seconds>\d+)\.(?P<microseconds>\d+)",
    "DASHIFY_VIDEO_TRANSCODE_COMMAND": "{ffmpeg} -y -hide_banner -i {input} -an -c:v libx264 -r {framerate} -b:v:{stream} {bitrate}k -maxrate {maxrate}k -bufsize {bufsize}k -preset {preset} -x264opts keyint={keyint}:min-keyint={keyint}:no-scenecut -vf scale={width}:{height} -movflags +faststart {output}",
    "DASHIFY_AUDIO_TRANSCODE_COMMAND": "{ffmpeg} -y -hide_banner -i {input} -vn -c:a:{stream} {codec} -ac {channels} -ab {bitrate}k {output}",
    "DASHIFY_PACK_COMMAND": "{mp4box} -dash {segsize} -rap -bs-switching no -profile {profile} -out {output} {input}",

    "DASHIFY_FFMPEG_BIN": "ffmpeg",
    "DASHIFY_FFPROBE_BIN": "ffprobe",
    "DASHIFY_MP4BOX_BIN": "MP4Box"
}


def load_video_config(path):

    try:
        with open(path + ".dashify.config", "rb") as raw_video_config:
            return json.load(raw_video_config)

    except IOError:
        return {}


def register_settings(pelican):

    for k, v in DEFAULT_CONFIG.iteritems():
        pelican.settings.setdefault(k, v)
