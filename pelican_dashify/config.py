import json

DEFAULT_CONFIG = {
    "METATAG": "{dashify}",
    "EXTRACT_TAGS": True,
    "CACHE_PATH": None,
    # bitrate computed from 0.1bpp @ 24fps
    "VIDEO_MAX_WIDTH": 7680,
    "VIDEO_MAX_HEIGHT": 4320,
    "VIDEO_MAX_BITRATE": 79626,
    "VIDEO_MIN_WIDTH": 128,
    "VIDEO_MIN_HEIGHT": 72,
    "VIDEO_MIN_BITRATE": 22,
    "RESOLUTION_DIVISOR": 2,
    "SEGMENT_DURATION": 4,
    "BITS_PER_PIXEL": 0.1,
    "FRAMERATE": 24,
    "X264_PRESET": "slow",
    "DASH_PROFILE": "onDemand",
    "VIDEO_REPRESENTATIONS": 3,
    "VIDEO_STREAM_INDEX": 0,
    "AUDIO_CODEC": "aac",
    "AUDIO_CHANNELS": 2,
    "AUDIO_BITRATE": 128,  # in kbps
    "AUDIO_DISABLE": False,
    "AUDIO_STREAM_INDEX": 0,
    "INFO_COMMAND": (
        "{ffprobe} -v quiet -print_format json "
        "-show_format -show_streams -sexagesimal {input}"
    ),
    "SEXAGESIMAL_REGEX": (
        r"(?P<hours>\d+):(?P<minutes>\d+)+"
        r":(?P<seconds>\d+)\.(?P<microseconds>\d+)"
    ),
    "VIDEO_TRANSCODE_COMMAND": (
        "{ffmpeg} -y -hide_banner -i {input} "
        "-an -c:v libx264 -r {framerate} "
        "-b:v:{stream} {bitrate}k "
        "-maxrate {maxrate}k "
        "-bufsize {bufsize}k "
        "-preset {preset} "
        "-x264opts keyint={keyint}:min-keyint={keyint}:no-scenecut "
        "-vf scale={width}:{height} "
        "-movflags +faststart {output}"
    ),
    "AUDIO_TRANSCODE_COMMAND": (
        "{ffmpeg} -y -hide_banner -i {input} "
        "-vn -c:a:{stream} {codec} "
        "-ac {channels} -ab {bitrate}k {output}"
    ),
    "PACK_COMMAND": (
        "{mp4box} -dash {segsize} -rap -bs-switching no "
        "-profile {profile} -out {output} {input}"
    ),
    "FFMPEG_BIN": "ffmpeg",
    "FFPROBE_BIN": "ffprobe",
    "MP4BOX_BIN": "MP4Box",

    "PLAYER_AUTOPLAY": False,
    "PLAYER_CONTROLS": True,
    "PLAYER_MUTED": False,
    "PLAYER_LOOP": False,
    "PLAYER_CROSSORIGIN": False,
    "PLAYER_PLAYSINLINE": False,
    "PLAYER_PRELOAD": None,
    "PLAYER_POSTER": None,
    "PLAYER_HEIGHT": None,
    "PLAYER_WIDTH": None,
    "PLAYER_CLASS": None,
    "PLAYER_ID": None,
    "PLAYER_TEMPLATE": (
        # Jinja Template
        '<video src="{{ context.manifest_url }}"'
        '{{ " controls" if settings.PLAYER_CONTROLS else "" }}'
        '{{ " autoplay" if settings.PLAYER_AUTOPLAY else "" }}'
        '{{ " muted" if settings.PLAYER_MUTED else "" }}'
        '{{ " loop" if settings.PLAYER_LOOP else "" }}'
        '{{ " crossorigin" if settings.PLAYER_CROSSORIGIN else "" }}'
        '{{ " playsinline" if settings.PLAYER_PLAYSINLINE else "" }}'
        '{% if settings.PLAYER_POSTER %} poster="{{ context.poster_url }}"{% endif %}'
        '{% if settings.PLAYER_PRELOAD %} preload="{{ settings.PLAYER_PRELOAD }}"{% endif %}'
        '></video>'
    )
}

SETTING_PREFIX = "DASHIFY_"
settings = {}


def load_video_config(path):
    """Load video configuration file from video path"""
    try:
        with open(path + ".dashify.config", "rb") as raw_video_config:
            return json.load(raw_video_config)

    except IOError:
        return {}


def register_settings(pelican):
    """
    Loads and exposes plugin settings to pelican and to `dashify.config.settings`
    """
    global settings
    global_settings = {}
    # Registering the Dashify plugin settings to Pelican globals
    for k, v in DEFAULT_CONFIG.items():
        prefixed_key = "{}{}".format(SETTING_PREFIX, k)
        pelican.settings.setdefault(prefixed_key, v)
        global_settings[k] = pelican.settings[prefixed_key]
    settings = global_settings
