import re
p = 'service.py'
t = open(p, encoding='utf-8').read()

t = t.replace("import xbmc\nimport xbmcgui", "import xbmc\nimport xbmcgui\nimport xbmcvfs", 1)

old_resolve = '''    value = path.split('|', 1)[0].strip()
    if value.startswith('image://'):
        value = urllib.parse.unquote(value[len('image://'):])
        if value.endswith('/'):
            value = value[:-1]
    return value'''
new_resolve = '''    value = path.split('|', 1)[0].strip()
    if value.startswith('image://'):
        value = urllib.parse.unquote(value[len('image://'):])
    if value.endswith('/unknown.png'):
        value = value[:-len('/unknown.png')]
    if value.endswith('/'):
        value = value[:-1]
    return value'''
assert old_resolve in t
t = t.replace(old_resolve, new_resolve, 1)

old_read = """        with open(path, 'rb') as handle:
            head = handle.read()"""
new_read = """        try:
            with open(path, 'rb') as handle:
                head = handle.read()
        except OSError:
            head = b''
            handle = xbmcvfs.File(path)
            try:
                data = handle.readBytes()
                if isinstance(data, bytes):
                    head = data
            finally:
                handle.close()"""
assert old_read in t
t = t.replace(old_read, new_read, 1)

old_log = """        except Exception as error:            # noqa: BLE001 - never break playback
        log('could not inspect %s: %s' % (source[:120], error), xbmc.LOGWARNING)
        matted = False"""
if old_log in t:
    t = t.replace(old_log, old_log.replace('xbmc.LOGWARNING', 'xbmc.LOGDEBUG'), 1)
else:
    t = t.replace("log('could not inspect %s: %s' % (source[:120], error), xbmc.LOGWARNING)",
                  "log('could not inspect %s: %s' % (source[:120], error), xbmc.LOGDEBUG)", 1)

open(p, 'w', encoding='utf-8').write(t)
print('service.py patched: xbmcvfs support, safer URL handling')

p = 'addon.xml'
t = open(p, encoding='utf-8').read()
t = t.replace('version="1.4.0"', 'version="1.4.1"', 1)
open(p, 'w', encoding='utf-8').write(t)
print('addon -> 1.4.1')
