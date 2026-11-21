p = 'service.py'
t = open(p, encoding='utf-8').read()

t = t.replace("import xbmc\nimport xbmcgui", "import xbmc\nimport xbmcgui\nimport xbmcvfs", 1)

t = t.replace("""    else:
        with open(path, 'rb') as handle:
            head = handle.read(HEAD_BYTES)
    return head""",
"""    elif '://' in path:
        # dav:// smb:// nfs:// etc - read through Kodi's VFS
        handle = xbmcvfs.File(path)
        try:
            data = handle.readBytes()
            head = data if isinstance(data, bytes) else b''
        finally:
            handle.close()
    else:
        with open(path, 'rb') as handle:
            head = handle.read(HEAD_BYTES)
    return head""", 1)

t = t.replace("""    value = path.split('|', 1)[0].strip()
    if value.startswith('image://'):
        value = urllib.parse.unquote(value[len('image://'):])
        if value.endswith('/'):
            value = value[:-1]
    return value""",
"""    value = path.split('|', 1)[0].strip()
    if value.startswith('image://'):
        value = urllib.parse.unquote(value[len('image://'):])
    if value.endswith('/unknown.png'):
        value = value[:-len('/unknown.png')]
    if value.endswith('/'):
        value = value[:-1]
    return value""", 1)

t = t.replace("log('could not inspect %s: %s' % (source[:120], error), xbmc.LOGWARNING)",
              "log('could not inspect %s: %s' % (source[:120], error), xbmc.LOGDEBUG)", 1)

assert 'xbmcvfs.File' in t and 'unknown.png' in t
open(p, 'w', encoding='utf-8').write(t)
print('service.py patched')

p = 'addon.xml'
t = open(p, encoding='utf-8').read()
t = t.replace('version="1.4.0"', 'version="1.4.1"', 1)
open(p, 'w', encoding='utf-8').write(t)
print('addon -> 1.4.1')
