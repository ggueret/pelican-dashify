import os

CURRENT_PATH = os.path.realpath(__file__)
CURRENT_DIRECTORY = os.path.dirname(CURRENT_PATH)
PARENT_DIRECTORY = os.path.abspath(os.path.join(CURRENT_DIRECTORY, os.pardir))
EXAMPLE_DIRECTORY = os.path.join(PARENT_DIRECTORY, "example")


def test_project_example(tmp_path_factory):
    from pelican import Pelican, read_settings

    OUTPUT_PATH = str(tmp_path_factory.getbasetemp())

    settings = read_settings(
        os.path.join(EXAMPLE_DIRECTORY, "pelicanconf.py"),
        override={
            "PATH": os.path.join(EXAMPLE_DIRECTORY, "content"),
            "OUTPUT_PATH": OUTPUT_PATH
        })

    pelican = Pelican(settings)
    pelican.run()

    EXPECTED_FILES = [
        "videos/trailer_1080p.mov/.cache/1920x1080_4976k.mp4",
        "videos/trailer_1080p.mov/.cache/960x540_1244k.mp4",
        "videos/trailer_1080p.mov/.cache/480x270_311k.mp4",
        "videos/trailer_1080p.mov/.cache/audio_128k.mp4",
        "videos/trailer_1080p.mov/1920x1080_4976k_dash_track1_init.mp4",
        "videos/trailer_1080p.mov/960x540_1244k_dash_track1_init.mp4",
        "videos/trailer_1080p.mov/480x270_311k_dash_track1_init.mp4",
        "videos/trailer_1080p.mov/audio_128k_dash_track1_init.mp4",
        "videos/trailer_1080p.mov/manifest.mpd"
    ]

    for file_path in EXPECTED_FILES:
        assert os.path.isfile(os.path.join(OUTPUT_PATH, file_path))
