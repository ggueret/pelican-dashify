from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from jinja2 import Environment, BaseLoader
from .dashify import dashify_video


def boolean_option(argument):
    if not argument or not argument.strip():
        return True

    cleaned_argument = argument.strip().lower()
    if cleaned_argument in ("1", "true", "yes", "y"):
        return True
    elif cleaned_argument in ("0", "false", "no", "n"):
        return False

    raise ValueError(
        "unknown boolean value supplied, could be: "
        "(empty), 0/1, true/false, yes/no, y/n")


class Dashify(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    option_spec_player = {
        "autoplay": boolean_option,
        "controls": boolean_option,
        "muted": boolean_option,
        "loop": boolean_option,
        "crossorigin": boolean_option,
        "playsinline": boolean_option,
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
        "extract_tags": boolean_option,
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
        "audio_disable": boolean_option,
        "audio_stream_index": directives.positive_int
    }

    option_spec = {"path": directives.path}
    option_spec.update(option_spec_player)
    option_spec.update(option_spec_transcoding)

    def _load_settings(self):
        options = self._build_prefixed_options()
        return self._load_merged_settings(options)

    def _build_prefixed_options(self):
        """Transforms player options to """
        settings = {}
        for k, v in self.options.items():
            if k in self.option_spec_player:
                k = "PLAYER_{}".format(k)
            settings[k.upper()] = True if v is None else v
        return settings

    def _load_merged_settings(self, custom_settings):
        """
        Returns a dict containing settings built from global and customs.
        """
        from .config import settings as global_settings
        settings = global_settings.copy()
        settings.update(custom_settings)
        return settings

    def run(self):
        settings = self._load_settings()
        jinja_env = Environment(loader=BaseLoader)
        player_template = jinja_env.from_string(settings["PLAYER_TEMPLATE"])

        # handle custom HTML tag passed as content, render it with jinja
        if self.content:
            player_template = jinja_env.from_string('\n'.join(self.content))

        relpath = directives.path(self.arguments[0])
        player_context = dashify_video(relpath, **settings)

        # inject html options and video context to the HTML node
        self.options["path"] = relpath
        node = nodes.raw('', player_template.render(settings=settings, context=player_context), format="html")  # noqa: E501
        return [node]


def register_directives(pelican):
    directives.register_directive('dashify', Dashify)
