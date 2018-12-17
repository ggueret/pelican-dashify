Pelican-dashify
===============

Pelican-dashify let you to convert proper MPEG-DASH content generated from your videos with Pelican.


Features
--------

-	Support for MPEG-DASH live and on-demand profiles, and even [more](https://gpac.wp.imt.fr/mp4box/dash/).
-	Transcode a video stream in multiple qualities, customizable with settings.
-	Callable from any article or page metadata, by using the tag `{dashify}`.
-	Seamless integration with Pelican, dashify does not include any HTML or JS extra code.

### DASHwhat?

Many notable streming providers uses this [standard](https://tools.ietf.org/html/rfc6983), like YouTube or Netflix. MPEG-DASH let client adapt to changing network conditions and provide high quality playback with fewer stalls or re-buffering events. He is widely used on devices like Internet-connected televisions, TV set-top boxes, desktop computers, smartphones, tablets, etc. to consume multimedia content (video, TV, radio, etc.) delivered via the Internet.


Installation
------------

Under the hood, dashify call for external binaries, which are [ffprobe](https://www.ffmpeg.org/download.html) to get input file info like resolution and metainfo. [ffmpeg](https://www.ffmpeg.org/download.html) is used to transcode the representations and [MP4Box](https://gpac.wp.imt.fr/downloads/gpac-nightly-builds/) to pack everything for delivery. Tests will be added to cover supported versions list, for now `4.x` of ff[mpeg/probe] and `0.7.x` of GPAC are fine.

Install the latest release from PyPi :
```sh
pip install pelican-dashify
```


Quickstart
----------

Enable dashify for your Pelican project into the `pelicanconf.py` config file :
```python
PLUGINS = ('pelican_dashify',)
```

Download a video like the [Big Bunny](http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4) into the content directory, assuming path to be `content/videos/BigBuckBunny.mp4`.  
Edit a dummy article, with a "DASHified" version of the `BigBuckBunny.mp4` attached :


```restructuredtext
Big Buck Bunny
==============

:date: 2018-11-12 23:00
:summary: This is a MPEG-DASH compliant sample of the Big Buck Bunny
:video: {dashify}videos/BigBuckBunny.mp4
```

That's it, the site can be generated.
```
make html
```

### Generated files

Transcoded representations are stored in a cache-like directory to avoid a re-transcoding on every site generation.

```sh
output/videos/BigBuckBunny.mp4/.cache/1280x720_2211k.mp4
output/videos/BigBuckBunny.mp4/.cache/640x360_552k.mp4
output/videos/BigBuckBunny.mp4/.cache/320x180_138k.mp4
output/videos/BigBuckBunny.mp4/.cache/audio_128k.mp4
```

Since these files are stored in the Pelican output directory by default, they will be removed on cleaning, which leads to re-transcode. To avoid this behavior, set `DASHIFY_CACHE_PATH` outside the output scope.

Just after, on packing phase, representations are segmented by MP4Box and placed in the output directory.
From `BigBuckBunny.mp4`, using the default DASH profile 'onDemand', following files have been generated :

```sh
output/videos/BigBuckBunny.mp4/manifest.mpd
output/videos/BigBuckBunny.mp4/1280x720_2211k_dash_track1_init.mp4
output/videos/BigBuckBunny.mp4/640x360_552k_dash_track1_init.mp4
output/videos/BigBuckBunny.mp4/320x180_138k_dash_track1_init.mp4
output/videos/BigBuckBunny.mp4/audio_128k_dash_track1_init.mp4
```

To serve representations using the `onDemand` profile, the HTTP server must support range requests. As a workaround, the `live` profile can be used.

### Video displaying

Now the content has been generated, but Pelican doesn't know how and where to display the video. To do this, a modification of your template is required.
You can use any DASH player to read your converted video, for this example, we choose video.js for less code as possible.

Into `article.html` :
```jinja
{% extends "base.html" %}
...

{% block content %}
<section id="content" class="body">
  ...
  <div class="entry-content">
    {% if article.video %}
    <video data-dashjs-player autoplay src="{{ SITEURL }}/{{ article.video.url }}" controls></video>
    <div class="video-duration">{{ article.video.duration|timedelta_as_string }}</div>
    {% endif %}

    {{ article.content }}
  </div><!-- /.entry-content -->
</section>
<script src="https://cdn.dashjs.org/latest/dash.all.min.js"></script>
{% endblock %}
```

The `timedelta_as_string` are provided by Pelican-dashify.


Settings
--------

Settings can be defined globaly into `pelicanconf.py` or per video using a specific JSON file.
To define a video configuration, like a custom DASH profile for `BigBuckBunny.mp4`, create a file named `BigBuckBunny.mp4.dashify.config` with the following content :

```json
{
	"DASHIFY_DASH_PROFILE": "live"
}
```

### General

**DASHIFY_EXTRACT_TAGS**
:	Inject the original video tags into the template variable `{{ <metaname>.tags }}`. Default to `False`.

**DASHIFY_CACHE_PATH**
:	Use a custom path to store the representations transcoded from the original video.
	By default, dashify will store them into the content directory. Default to `None`.

**DASHIFY_FFMPEG_BIN**
:	Specific path to use for the ffmpeg binary, libav can be used. Default to `ffmpeg`.

**DASHIFY_FFPROBE_BIN**
:	Specific path to use for the ffprobe binary. Default to `ffprobe`.

**DASHIFY_MP4BOX_BIN**
:	Specific path to use for the MP4Box binary. Default to `MP4Box`.

**DASHIFY_METATAG**
:	Tag used to prefix video to be DASHified. Default to `{dashify}`.

### Transcoding

**DASHIFY_RESOLUTION_DIVISOR**
:	The divisor used to downscale the resolution of representations. Default is `2`.  
	For a 720p formatted input, the 1280x720, 640x360 and 320x180 will be generated with `DASHIFY_VIDEO_REPRESENTATIONS` set to 3.

**DASHIFY_VIDEO_REPRESENTATIONS**
:	How many representations to generate. Default to `3`.

**DASHIFY_SEGMENT_DURATION**
:	The time of a DASH segment in seconds, used to switch between the different video/audio qualities.  
	Dashify will compute the ffmpeg keyint accordingly. Default to `4`.

**DASHIFY_BITS_PER_PIXEL**
:	The BPP used to compute the bitrate for a given resolution. Default to `0.1`.

**DASHIFY_DASH_PROFILE**
:	Choices are : `onDemand`, `live`, `main`, `simple`, `full`, `dashavc264:live`, `dashavc264:onDemand`.  
	Default to `onDemand`.

### Video

**DASHIFY_FRAMERATE**
:	The frames per second to use on representations. Default to `24`fps.

**DASHIFY_X264_PRESET**
:	Preset used by ffmpeg on transcoding. Default to `slow` for a better rendering.  
	Choices are : `ultrafast`, `superfast`, `veryfast`, `faster`, `fast`, `medium`, `slow`, `slower`, `veryslow`.  
	For more info check the [ffmpeg wiki](https://trac.ffmpeg.org/wiki/Encode/H.264#Preset).

**DASHIFY_VIDEO_STREAM_INDEX**
:	Select a given stream from the input container. Default to `0` for the first available one.

**DASHIFY_VIDEO_MAX_WIDTH**
:	Skip representation if computed width is greater then value. Default to `7680` (8K).

**DASHIFY_VIDEO_MAX_HEIGHT**
:	Skip representation if computed height is greater then value. Default to `4320` (8K).

**DASHIFY_VIDEO_MAX_BITRATE**
:	Skip representation if computed bitrate is greater then value. Default to `79626` (8K w/ 0.1 BPP @ 24fps).

**DASHIFY_VIDEO_MIN_WIDTH**
:	Skip representation if computed width is lower then value. Default to `128`.

**DASHIFY_VIDEO_MIN_HEIGHT**
:	Skip representation if computed height is lower then value. Default to `72`.

**DASHIFY_VIDEO_MIN_BITRATE**
:	Skip representation if computed bitrate width is lower then value. Default to `22`.

### Audio

**DASHIFY_AUDIO_STREAM_INDEX**
:	Select a given stream from the input container. Default to `0` for the first available one.

**DASHIFY_AUDIO_CODEC**
:	Codec to use on audio transcoding. Default to `aac`.

**DASHIFY_AUDIO_CHANNELS**
:	Number of audio channels. Default to `2`.

**DASHIFY_AUDIO_BITRATE**
:	Default to `128`k.

**DASHIFY_AUDIO_DISABLE**
:	Disable audio. Default to `False`.
