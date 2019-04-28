import os

CURRENT_PATH = os.path.realpath(__file__)
CURRENT_DIRECTORY = os.path.dirname(CURRENT_PATH)
PARENT_DIRECTORY = os.path.abspath(os.path.join(CURRENT_DIRECTORY, os.pardir))
EXAMPLE_DIRECTORY = os.path.join(PARENT_DIRECTORY, "example")


def test_project_example(tmp_path_factory):
    from pelican import Pelican, read_settings

    OUTPUT_PATH = tmp_path_factory.getbasetemp()

    settings = read_settings(
        os.path.join(EXAMPLE_DIRECTORY, "pelicanconf.py"),
        override={
            "PATH": os.path.join(EXAMPLE_DIRECTORY, "content"),
            "OUTPUT_PATH": str(OUTPUT_PATH)
        })

    pelican = Pelican(settings)
    pelican.run()

    assert len(list(OUTPUT_PATH.glob("videos/trailer_1080p.mov/.cache/*.mp4"))) == 4  # noqa: E501
    assert len(list(OUTPUT_PATH.glob("videos/trailer_1080p.mov/*.mp4"))) == 4
    assert OUTPUT_PATH.joinpath("videos/trailer_1080p.mov/manifest.mpd").is_file()
    # todo: read the manifest to validate related files
