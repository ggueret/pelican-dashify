class VideoProbeError(Exception):
    pass


class VideoStreamError(Exception):
    pass


class TranscodeError(Exception):
    pass


class PackingError(Exception):
    pass


class AudioTranscodeError(TranscodeError):
    pass


class VideoTranscodeError(TranscodeError):
    pass
