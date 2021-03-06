import os
import re
import sys
import json
import shlex
import logging
import datetime
import subprocess as sp

from .settings import DEFAULT_CONFIG, load_video_config
from .exceptions import (
    AudioTranscodeError,
    PackingError,
    VideoProbeError,
    VideoStreamError,
    VideoTranscodeError
)

SETTINGS_PREFIX = "DASHIFY_"


def select_stream_by_typed_index(ffprobe_streams, index, codec_type=None):
    """will return the mixed position of a stream by codec type"""
    assert codec_type in ("audio", "video")

    current_type_index = -1

    for stream in ffprobe_streams:

        if stream["codec_type"] == codec_type:
            current_type_index += 1

        if current_type_index == index:
            return int(stream["index"])


def run_command(command, stdout=sp.PIPE, stderr=sp.PIPE, *args, **kwargs):
    """Run an external process with a specific command"""
    if isinstance(command, str):
        command = shlex.split(command)

    process = sp.Popen(command, stdout=stdout, stderr=stderr)
    stdout, stderr = process.communicate()
    return (process.returncode, stdout, stderr)


def generate_video_representations(input_path, stream_info, settings):
    def compute_bitrate(width, height):
        fps = settings["FRAMERATE"]
        bpp = settings["BITS_PER_PIXEL"]
        return int(width * height * fps * bpp) // 1000

    input_width = int(stream_info["width"])
    input_height = int(stream_info["height"])

    for i in range(settings["VIDEO_REPRESENTATIONS"]):
        repr_divisor = settings["RESOLUTION_DIVISOR"] * i or 1
        output_width = input_width // repr_divisor
        output_height = input_height // repr_divisor

        min_bitrate = settings["VIDEO_MIN_BITRATE"]
        min_width = settings["VIDEO_MIN_WIDTH"]
        min_height = settings["VIDEO_MIN_HEIGHT"]
        max_bitrate = settings["VIDEO_MAX_BITRATE"]
        max_width = settings["VIDEO_MAX_WIDTH"]
        max_height = settings["VIDEO_MAX_HEIGHT"]

        if output_width > max_width or output_height > max_height:
            logging.warning(
                "Skip %dx%d format of %s, resolution greater then the max.",
                output_width, output_height, input_path
            )
            continue

        if output_width < min_width or output_height < min_height:
            logging.warning(
                "Skip %dx%d format of %s, resolution lower than the min.",
                output_width, output_height, input_path
            )
            continue

        output_bitrate = compute_bitrate(output_width, output_height)

        if output_bitrate > max_bitrate or output_bitrate < min_bitrate:
            logging.warning(
                "Skip %dx%d@%dk representation of %s, bitrate limit reached.",
                output_width,
                output_height,
                output_bitrate,
                input_path
            )
            continue

        yield (output_width, output_height, output_bitrate)


def load_input_info(path, settings):

    retcode, stdout, stderr = run_command(
        settings["INFO_COMMAND"].format(
            ffprobe=settings["FFPROBE_BIN"], input=path
        )
    )

    if retcode != 0:
        raise VideoProbeError(
            "ffprobe failed with code {}, stderr: {}".format(retcode, stderr)
        )

    return json.loads(stdout.decode(sys.stdout.encoding))


def transcode_audio_stream(input_path, output_path, stream, bitrate, settings):

    command = settings["AUDIO_TRANSCODE_COMMAND"].format(
        ffmpeg=settings["FFMPEG_BIN"],
        input=input_path,
        output=output_path,
        stream=stream,
        codec=settings["AUDIO_CODEC"],
        channels=settings["AUDIO_CHANNELS"],
        bitrate=bitrate
    )
    retcode, stdout, stderr = run_command(command)

    if retcode != 0:
        raise AudioTranscodeError(
            "ffmpeg return code {}, stderr: {}".format(retcode, stderr)
        )


def transcode_video_stream(input_path, output_path, stream, width, height, bitrate, settings):  # noqa: E501

    command = settings["VIDEO_TRANSCODE_COMMAND"].format(
        ffmpeg=settings["FFMPEG_BIN"],
        input=input_path,
        output=output_path,
        stream=stream,
        width=width,
        height=height,
        bitrate=bitrate,
        maxrate=(bitrate * 2),
        bufsize=(bitrate * 4),
        keyint=(settings["FRAMERATE"] * settings["SEGMENT_DURATION"]),
        preset=settings["X264_PRESET"],
        framerate=settings["FRAMERATE"]
    )
    retcode, stdout, stderr = run_command(command)

    if retcode != 0:
        raise VideoTranscodeError(
            "ffmpeg return code {}, stderr: {}".format(retcode, stderr)
        )


def generate_dash_manifest(representations, output_path, settings):

    command = settings["PACK_COMMAND"].format(
        mp4box=settings["MP4BOX_BIN"],
        input=" ".join(representations),
        output=output_path,
        profile=settings["DASH_PROFILE"],
        segsize=settings["SEGMENT_DURATION"] * 1000
    )
    retcode, stdout, stderr = run_command(command)

    if retcode != 0:
        raise PackingError(
            "MP4Box return code {}, sderr: {}".format(retcode, stderr))


def dashify_video(generator, content, input_relpath, keyword):

    input_path = os.path.join(generator.path, input_relpath)
    output_dir = os.path.join(generator.output_path, input_relpath)

    if not os.path.isfile(input_path):
        raise VideoProbeError("The file '{}' does not exist.".format(input_path))  # noqa: E501

    pad = len(SETTINGS_PREFIX)
    settings = {k[pad:]: content.settings[k] for k in DEFAULT_CONFIG.keys()}
    settings.update(load_video_config(input_path))

    input_info = load_input_info(input_path, settings)
    output_info = {}

    video_index = select_stream_by_typed_index(
        input_info["streams"],
        settings["VIDEO_STREAM_INDEX"],
        codec_type="video"
    )

    if video_index is None:
        raise VideoStreamError(
            "cannot find a valid video stream with index %{}".format(
                settings["VIDEO_STREAM_INDEX"]
            )
        )

    sexagesimal_parsed = re.match(
        settings["SEXAGESIMAL_REGEX"], input_info["format"]["duration"]
    ).groupdict()
    # fixme
    output_info["duration"] = datetime.timedelta(
        **{k: int(v) for k, v in sexagesimal_parsed.items()}
    )

    if settings["EXTRACT_TAGS"]:
        # todo: python native types
        output_info["tags"] = input_info["format"]["tags"]

    # todo: generate previews

    if settings["CACHE_PATH"]:
        cache_dir = os.path.abspath(
            os.path.join(settings["CACHE_PATH"], input_relpath)
        )
    else:
        cache_dir = os.path.join(output_dir, ".cache")

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    output_presets = list(
        generate_video_representations(
            input_path, input_info["streams"][video_index], settings
        )
    )
    output_paths = []

    if not settings["AUDIO_DISABLE"]:
        audio_index = select_stream_by_typed_index(
            input_info["streams"],
            settings["AUDIO_STREAM_INDEX"],
            codec_type="audio"
        )
        output_filename = "audio_{}k.mp4".format(settings["AUDIO_BITRATE"])
        output_path = os.path.join(cache_dir, output_filename)
        output_paths.append(output_path + "#audio")

        if not os.path.exists(output_path):
            logging.info(
                "Transcoding audio representation %s from %s",
                output_filename,
                input_relpath,
            )
            transcode_audio_stream(
                input_path,
                output_path,
                audio_index,
                settings["AUDIO_BITRATE"],
                settings,
            )

    for width, height, bitrate in output_presets:
        output_filename = "{0}x{1}_{2}k.mp4".format(width, height, bitrate)
        output_path = os.path.join(cache_dir, output_filename)
        output_paths.append(output_path + "#video")

        if os.path.exists(output_path):
            continue

        logging.info("Transcoding video %s from %s", output_filename, input_relpath)  # noqa: E501
        transcode_video_stream(
            input_path, output_path, video_index,
            width, height, bitrate, settings
        )

    manifest_name = "manifest.mpd"
    manifest_path = os.path.join(output_dir, manifest_name)

    if not os.path.exists(manifest_path):
        logging.info("Generate DASH manifest for %s", input_relpath)
        generate_dash_manifest(output_paths, manifest_path, settings)

    output_info["url"] = os.path.join(input_relpath, manifest_name)

    setattr(content, keyword, output_info)


def discover_dashify(generator, content):

    for k, v in content.metadata.items():
        METATAG = content.settings["{}METATAG".format(SETTINGS_PREFIX)]

        if isinstance(v, str) and v.startswith(METATAG):
            input_relpath = v.strip(METATAG)

            try:
                dashify_video(generator, content, input_relpath, k)

            except Exception:
                logging.exception("dashify errored")


def dashify_videos(generators):

    articles_generator, pages_generator = generators[0:2]

    for article in articles_generator.articles:
        discover_dashify(articles_generator, article)

    for page in pages_generator.pages:
        discover_dashify(pages_generator, page)
