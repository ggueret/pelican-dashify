from pelican import signals
from .dashify import dashify_videos
from .filters import register_filters
from .settings import register_settings


def register():

    signals.initialized.connect(register_filters)
    signals.initialized.connect(register_settings)
    signals.all_generators_finalized.connect(dashify_videos)
