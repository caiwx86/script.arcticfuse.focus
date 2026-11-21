# -*- coding: utf-8 -*-
"""Arctic Fuse 3 logo matte detector.

Instead of guessing from the file extension this reads the actual image data
(local file or HTTP range request) and checks whether the picture even has an
alpha channel:

    no alpha channel  ->  the transparent parts were flattened onto black
    alpha channel     ->  usable as a transparent logo

The result is published for the skin as

    Window(Home).Property(ArcticFuse.Logo.Matted) = "true" / "false"
"""
import struct
import time
import urllib.parse
import urllib.request

import xbmc
import xbmcgui

ADDON_ID = 'script.arcticfuse.focus'
PROPERTY = 'ArcticFuse.Logo.Matted'
WINDOW = xbmcgui.Window(10000)

FALLBACK_LABELS = (
    'Player.Art(clearlogo)',
    'Player.Art(tvshow.clearlogo)',
    'Player.Art(artist.clearlogo)',
)
HEAD_BYTES = 8192
CACHE = {}
CACHE_TTL = 300.0


def log(message, level=xbmc.LOGINFO):
    xbmc.log('[%s] %s' % (ADDON_ID, message), level)


def resolve_source(path):
    """Turn an art label into something we can read bytes from."""
    if not path:
        return ''
    value = path.split('|', 1)[0].strip()
    if value.startswith('image://'):
        value = urllib.parse.unquote(value[len('image://'):])
        if value.endswith('/'):
            value = value[:-1]
    return value


def read_head(path):
    head = b''
    if path.startswith(('http://', 'https://')):
        request = urllib.request.Request(path, headers={
            'Range': 'bytes=0-%d' % (HEAD_BYTES - 1),
            'User-Agent': 'Kodi/%s' % xbmc.getInfoLabel('System.BuildVersion').split(' ')[0],
        })
        with urllib.request.urlopen(request, timeout=4) as response:
            head = response.read(HEAD_BYTES)
    else:
        with open(path, 'rb') as handle:
            head = handle.read(HEAD_BYTES)
    return head


def png_has_alpha(head):
    position = 8
    while position + 8 <= len(head):
        length = struct.unpack('>I', head[position:position + 4])[0]
        chunk = head[position + 4:position + 8]
        if chunk == b'IHDR':
            color_type = head[position + 8 + 9]
            return color_type in (4, 6)
        if chunk == b'tRNS':
            return True
        if chunk in (b'IDAT', b'IEND'):
            return False
        position += 12 + length
    return False


def webp_has_alpha(head):
    if head[12:16] == b'VP8X':
        return bool(head[20] & 0x10)
    return b'ALPH' in head


def has_alpha(head):
    if not head:
        return True
    if head[:8] == b'\x89PNG\r\n\x1a\n':
        return png_has_alpha(head)
    if head[:2] == b'\xff\xd8':
        return False                      # JPEG: no alpha channel at all
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return webp_has_alpha(head)
    if head[:6] in (b'GIF87a', b'GIF89a'):
        return True                       # palette transparency, assume usable
    return True                           # unknown container: do not block the logo


def is_matted(path):
    source = resolve_source(path)
    if not source:
        return False
    cached = CACHE.get(source)
    now = time.time()
    if cached and now - cached[1] < CACHE_TTL:
        return cached[0]
    try:
        matted = not has_alpha(read_head(source))
    except Exception as error:            # noqa: BLE001 - never break playback
        log('could not inspect %s: %s' % (source[:120], error), xbmc.LOGWARNING)
        matted = False
    CACHE[source] = (matted, now)
    return matted


def current_fallback_logo():
    for label in FALLBACK_LABELS:
        value = xbmc.getInfoLabel(label)
        if value:
            return value
    return ''


def main():
    monitor = xbmc.Monitor()
    last = None
    while not monitor.abortRequested():
        try:
            if xbmc.Player().isPlayingVideo():
                matted = 'true' if is_matted(current_fallback_logo()) else 'false'
                if matted != last:
                    WINDOW.setProperty(PROPERTY, matted)
                    last = matted
                    log('fallback clearlogo matted=%s' % matted)
            elif last is not None:
                WINDOW.clearProperty(PROPERTY)
                last = None
        except Exception as error:        # noqa: BLE001 - a service must never die
            log('logo detector error: %s' % error, xbmc.LOGWARNING)
        if monitor.waitForAbort(1.0):
            break


if __name__ == '__main__':
    main()
