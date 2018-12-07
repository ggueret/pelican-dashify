from __future__ import division
from __future__ import unicode_literals

import os
import re
import json
import shlex
import logging
import datetime
import subprocess

from .settings import DEFAULT_CONFIG, load_video_config
from .exceptions import VideoProbeError, VideoStreamError, PackingError, AudioTranscodeError, VideoTranscodeError


def select_stream_by_typed_index(ffprobe_streams, index, codec_type=None):
    """will return the mixed position of a stream by codec type"""
    assert codec_type in ("audio", "video")

    current_type_index = -1

    for stream in ffprobe_streams:

        if stream["codec_type"] == codec_type:
            current_type_index += 1

        if current_type_index == index:
            return int(stream["index"])


def run_command(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, *args, **kwargs):

    if isinstance(command, unicode):
        command = shlex.split(command)

    process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
    stdout, stderr = process.communicate()
    return (process.returncode, stdout, stderr)


def generate_video_representations(input_path, stream_info, settings):

    def compute_bitrate(width, height):
        fps = settings["DASHIFY_FRAMERATE"]
        bpp = settings["DASHIFY_BITS_PER_PIXEL"]
        return int(width * height * fps * bpp) // 1000

    input_width = int(stream_info["width"])
    input_height = int(stream_info["height"])

    for i in range(settings["DASHIFY_VIDEO_REPRESENTATIONS"]):
        repr_divisor = settings["DASHIFY_RESOLUTION_DIVISOR"] * i or 1
        output_width = input_width // repr_divisor
        output_height = input_height // repr_divisor

        if output_width > settings["DASHIFY_VIDEO_MAX_WIDTH"] or output_height > settings["DASHIFY_VIDEO_MAX_HEIGHT"]:
            logging.warning("Skip %dx%d representation of %s, resolution greater then max.", output_width, output_height, input_path)
            continue

        elif output_width < settings["DASHIFY_VIDEO_MIN_WIDTH"] or output_height < settings["DASHIFY_VIDEO_MIN_HEIGHT"]:
            logging.warning("Skip %dx%d representation of %s, resolution lower than min.", output_width, output_height, input_path)
            continue

        output_bitrate = compute_bitrate(output_width, output_height)

        if output_bitrate > settings["DASHIFY_VIDEO_MAX_BITRATE"] or output_bitrate < settings["DASHIFY_VIDEO_MIN_BITRATE"]:
            logging.warning("Skip %dx%d@%dk representation of %s, bitrate limit reached.", output_width, output_height, output_bitrate, input_path)
            continue

        yield (output_width, output_height, output_bitrate)


def load_input_info(path, settings):

    retcode, stdout, stderr = run_command(settings["DASHIFY_INFO_COMMAND"].format(
        ffprobe=settings["DASHIFY_FFPROBE_BIN"],
        input=path
    ))

    if retcode != 0:
        raise VideoProbeError("ffprobe failed with code {}, stderr: {}".format(retcode, stderr))

    return json.loads(stdout)


def transcode_audio_stream(input_path, output_path, stream, bitrate, settings):

    command = settings["DASHIFY_AUDIO_TRANSCODE_COMMAND"].format(
        ffmpeg=settings["DASHIFY_FFMPEG_BIN"],
        input=input_path,
        output=output_path,
        stream=stream,
        codec=settings["DASHIFY_AUDIO_CODEC"],
        channels=settings["DASHIFY_AUDIO_CHANNELS"],
        bitrate=bitrate
    )
    retcode, stdout, stderr = run_command(command)

    if retcode is not 0:
        raise AudioTranscodeError("ffmpeg return code {}, stderr: {}".format(retcode, stderr))


def transcode_video_stream(input_path, output_path, stream, width, height, bitrate, settings):

    command = settings["DASHIFY_VIDEO_TRANSCODE_COMMAND"].format(
        ffmpeg=settings["DASHIFY_FFMPEG_BIN"],
        input=input_path,
        output=output_path,
        stream=stream,
        width=width,
        height=height,
        bitrate=bitrate,
        maxrate=(bitrate * 2),
        bufsize=(bitrate * 4),
        keyint=(settings["DASHIFY_FRAMERATE"] * settings["DASHIFY_SEGMENT_DURATION"]),
        preset=settings["DASHIFY_X264_PRESET"],
        framerate=settings["DASHIFY_FRAMERATE"]
    )
    retcode, stdout, stderr = run_command(command)

    if retcode is not 0:
        raise VideoTranscodeError("ffmpeg return code {}, stderr: {}".format(retcode, stderr))


def generate_dash_manifest(representations, output_path, settings):

    command = settings["DASHIFY_PACK_COMMAND"].format(
        mp4box=settings["DASHIFY_MP4BOX_BIN"],
        input=" ".join(representations),
        output=output_path,
        profile=settings["DASHIFY_DASH_PROFILE"],
        segsize=settings["DASHIFY_SEGMENT_DURATION"] * 1000,
    )
    retcode, stdout, stderr = run_command(command)

    if retcode is not 0:
        raise PackingError("MP4Box return code {}, sderr: {}".format(retcode, stderr))


def dashify_video(generator, content, input_relpath, keyword):

    input_path = os.path.join(generator.path, input_relpath)
    output_dir = os.path.join(generator.output_path, input_relpath)

    if not os.path.isfile(input_path):
        raise VideoProbeError("The file '{}' does not exist.".format(input_path))

    settings = {k: content.settings[k] for k in DEFAULT_CONFIG.iterkeys()}
    settings.update(load_video_config(input_path))

    input_info = load_input_info(input_path, settings)
    output_info = {}

    video_index = select_stream_by_typed_index(input_info["streams"], settings["DASHIFY_VIDEO_STREAM_INDEX"], codec_type="video")

    if video_index is None:
        raise VideoStreamError("cannot find a valid video stream with index %{}".format(settings["DASHIFY_VIDEO_STREAM_INDEX"]))

    sexagesimal_parsed = re.match(settings["DASHIFY_SEXAGESIMAL_REGEX"], input_info["format"]["duration"]).groupdict()
    output_info["duration"] = datetime.timedelta(**{k: int(v) for k, v in sexagesimal_parsed.iteritems()})

    if settings["DASHIFY_EXTRACT_TAGS"]:
        # todo: python native types
        output_info["tags"] = input_info["format"]["tags"]

    # todo: generate previews

    if settings["DASHIFY_CACHE_PATH"]:
        cache_dir = os.path.abspath(os.path.join(settings["DASHIFY_CACHE_PATH"], input_relpath))
    else:
        cache_dir = os.path.join(output_dir, ".cache")

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    output_presets = list(generate_video_representations(input_path, input_info["streams"][video_index], settings))
    output_paths = []

    if not settings["DASHIFY_AUDIO_DISABLE"]:
        audio_index = select_stream_by_typed_index(input_info["streams"], settings["DASHIFY_AUDIO_STREAM_INDEX"], codec_type="audio")
        output_filename = "audio_{}k.mp4".format(settings["DASHIFY_AUDIO_BITRATE"])
        output_path = os.path.join(cache_dir, output_filename)
        output_paths.append(output_path + "#audio")

        if not os.path.exists(output_path):
            logging.info("Transcoding audio representation %s from %s", output_filename, input_relpath)
            transcode_audio_stream(input_path, output_path, audio_index, settings["DASHIFY_AUDIO_BITRATE"], settings)

    for width, height, bitrate in output_presets:
        output_filename = "{0}x{1}_{2}k.mp4".format(width, height, bitrate)
        output_path = os.path.join(cache_dir, output_filename)
        output_paths.append(output_path + "#video")

        if os.path.exists(output_path):
            continue

        logging.info("Transcoding video representation %s from %s", output_filename, input_relpath)
        transcode_video_stream(input_path, output_path, video_index, width, height, bitrate, settings)

    manifest_name = "manifest.mpd"
    manifest_path = os.path.join(output_dir, manifest_name)

    if not os.path.exists(manifest_path):
        logging.info("Generate DASH manifest for %s", input_relpath)
        generate_dash_manifest(output_paths, manifest_path, settings)

    output_info["url"] = os.path.join(input_relpath, manifest_name)

    setattr(content, keyword, output_info)


def discover_dashify(generator, content):

    for k, v in content.metadata.iteritems():

        if isinstance(v, unicode) and v.startswith(content.settings["DASHIFY_METATAG"]):
            input_relpath = v.strip(content.settings["DASHIFY_METATAG"])

            try:
                dashify_video(generator, content, input_relpath, k)

            except Exception:
                logging.exception("dashify errored")


def dashify_videos(generators):

    articles_generator, pages_generator = generators[0:2]

    for article in articles_generator.articles:
        discover_dashify(articles_generator, article)

    for page in pages_generator.pages:
        discover_dashify(articles_generator, article)
