from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from jinja2 import Environment, BaseLoader
from .dashify import dashify_video


class Dashify(Directive):
    # TODO: rename stream as track, eg `audio_stream_index`
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    option_spec_html = {
        # video node options
        "autoplay": directives.flag,
        "controls": directives.flag,
        "muted": directives.flag,
        "loop": directives.flag,
        "crossorigin": directives.flag,
        "playsinline": directives.flag,
        "preload": lambda arg: directives.choice(arg, (
            "none", "metadata", "auto"
        )),
        "poster": directives.path,
        "height": directives.nonnegative_int,
        "width": directives.nonnegative_int,
        "class": directives.unchanged,
        "id": directives.unchanged
    }
    option_spec_transcoding = {
        "extract_tags": directives.flag,
        "segment_duration": directives.positive_int,
        "bits_per_pixels": float,
        "framerate": directives.positive_int,
        "x264_preset": lambda arg: directives.choice(arg, (
            "slow", "fast")
        ),  # TODO: more presets
        "dash_profile": lambda arg: directives.choice(arg, (
            "ondemand", "live", "main", "simple", "full",
            "dashavc264:live", "dashavc264:onDemand"
        )),
        "video_representations": directives.positive_int,
        "video_stream_index": directives.positive_int,
        "audio_codec": lambda arg: directives.choice(arg, (
            "aac", "libfdk_aac"
        )),
        "audio_channels": directives.positive_int,
        "audio_bitrate": directives.positive_int,
        "audio_disable": directives.flag,
        "audio_stream_index": directives.positive_int
    }

    option_spec = {"path": directives.path}
    option_spec.update(option_spec_html)
    option_spec.update(option_spec_transcoding)

    def run(self):
        from . import pelican
        jinja_env = Environment(loader=BaseLoader)
        html_tag = jinja_env.from_string(pelican.settings["DASHIFY_HTML_TAG"])

        # handle custom HTML tag passed as content, render it with jinja
        if self.content:
            html_tag = jinja_env.from_string('\n'.join(self.content))

        relpath = directives.path(self.arguments[0])
        video_context = dashify_video(relpath, **self.options)

        # inject html options and video context to the HTML node
        self.options["path"] = relpath
        html_opts_and_context = self.options.copy()
        html_opts_and_context.update(video_context)
        node = nodes.raw('', html_tag.render(**html_opts_and_context), format="html")  # noqa: E501
        return [node]


def register_directives(pelican):
    directives.register_directive('dashify', Dashify)
