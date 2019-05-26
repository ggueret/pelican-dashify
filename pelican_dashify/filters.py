def timedelta_as_string(td):
    """Formatted 'HH:MM:SS' representation of a timedelta object"""
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return "{:02d}:{:02d}:{:02d}".format(*map(int, (hours, minutes, seconds)))


def register_filters(pelican):
    pelican.settings["JINJA_FILTERS"]["timedelta_as_string"] = timedelta_as_string
