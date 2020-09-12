from pelican import signals
from .config import register_settings
from .dashify import dashify_videos
from .filters import register_filters
from .directives import register_directives


pelican = None


def register_pelican(instance):
    """Exposing a (read-only) Pelican instance to Dashify"""
    global pelican
    pelican = instance


def register():
    """Registering the whole Dashify plugin"""
    signals.initialized.connect(register_pelican)
    signals.initialized.connect(register_directives)
    signals.initialized.connect(register_filters)
    signals.initialized.connect(register_settings)
    signals.all_generators_finalized.connect(dashify_videos)
