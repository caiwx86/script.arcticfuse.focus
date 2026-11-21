# -*- coding: utf-8 -*-
"""Arctic Fuse 3 logo matte detector.

Kodi cannot inspect pixels from skin XML, so a tiny service classifies the
clearlogo that the skin would fall back to (the library artwork) and publishes
the result as a window property:

    Window(Home).Property(ArcticFuse.Logo.Matted) = "true" / "false"

Info_Title uses that property to skip a black-matted JPEG logo and fall back to
the next source (online transparent logo, otherwise the text title).
"""
import xbmc
import xbmcgui

ADDON_ID = 'script.arcticfuse.focus'
PROPERTY = 'ArcticFuse.Logo.Matted'
WINDOW = xbmcgui.Window(10000)

# Only the fallback (library artwork) matters: the online TMDbHelper logos are PNG.
FALLBACK_LABELS = (
    'Player.Art(clearlogo)',
    'Player.Art(tvshow.clearlogo)',
    'Player.Art(artist.clearlogo)',
)


def log(message, level=xbmc.LOGINFO):
    xbmc.log('[%s] %s' % (ADDON_ID, message), level)


def is_matted(path):
    """A JPEG has no alpha channel, so Emby/HTTP JPEG logos carry a black matte."""
    if not path:
        return False
    clean = path.split('?', 1)[0].split('|', 1)[0].strip().lower()
    return clean.endswith(('.jpg', '.jpeg'))


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
        except Exception as error:  # noqa: BLE001 - a service must never die
            log('logo detector error: %s' % error, xbmc.LOGWARNING)
        if monitor.waitForAbort(1.0):
            break


if __name__ == '__main__':
    main()
