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

PLAYER_LABELS = (
    'Player.Art(clearlogo)',
    'Player.Art(tvshow.clearlogo)',
    'Player.Art(artist.clearlogo)',
)
LISTITEM_LABELS = (
    'ListItem.Art(clearlogo)',
    'ListItem.Art(tvshow.clearlogo)',
    'ListItem.Art(artist.clearlogo)',
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
        with urllib.request.urlopen(request, timeout=6) as response:
            head = response.read()
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
        if not png_has_alpha(head):
            return False
        return not bool(_opaque_black_edges(head))
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
    labels = PLAYER_LABELS if xbmc.Player().isPlayingVideo() else LISTITEM_LABELS
    for label in labels:
        value = xbmc.getInfoLabel(label)
        if value:
            return value
    return ''



def _png_rows(head):
    """Decode a small 8-bit non-interlaced PNG into (width, height, bpp, rows)."""
    import zlib
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        return None
    pos, idat, w = 8, b'', None
    while pos + 8 <= len(head):
        length = struct.unpack('>I', head[pos:pos + 4])[0]
        chunk = head[pos + 4:pos + 8]
        data = head[pos + 8:pos + 8 + length]
        if chunk == b'IHDR':
            w, h, depth, color, comp, filt, inter = struct.unpack('>IIBBBBB', data)
            if depth != 8 or inter != 0 or color not in (2, 6):
                return None
            bpp = 3 if color == 2 else 4
        elif chunk == b'IDAT':
            idat += data
        elif chunk == b'IEND':
            break
        pos += 12 + length
    if not w:
        return None
    try:
        raw = zlib.decompress(idat)
    except Exception:
        return None
    stride = w * bpp
    rows, prev, off = [], bytearray(stride), 0
    for _ in range(h):
        ftype = raw[off]
        off += 1
        line = bytearray(raw[off:off + stride])
        off += stride
        if ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xff
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xff
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xff
        elif ftype == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xff
        rows.append(bytes(line))
        prev = line
    return w, h, bpp, rows


def _opaque_black_edges(head):
    """True when the picture is effectively opaque black at its edges (baked matte)."""
    decoded = _png_rows(head)
    if not decoded:
        return None
    w, h, bpp, rows = decoded
    samples = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    for x, y in samples:
        px = rows[y][x * bpp:(x + 1) * bpp]
        if bpp == 4 and px[3] < 250:
            return False
        if max(px[0], px[1], px[2]) > 24:
            return False
    return True


def main():
    monitor = xbmc.Monitor()
    last = None
    while not monitor.abortRequested():
        try:
            logo = current_fallback_logo()
            if logo:
                matted = 'true' if is_matted(logo) else 'false'
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
