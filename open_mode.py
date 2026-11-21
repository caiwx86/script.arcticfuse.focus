import re

p = 'default.py'
t = open(p, encoding='utf-8').read()

# 1) new open mode: activate the window with the focus already on the playing entry
func = '''def open_playlist(window_id, control_id):
    """Open the OSD playlist with focus already on the playing entry (no visible jump)."""
    position = as_int(info('VideoPlayer.PlaylistPosition'), 1)
    index = max(position - 1, 0)
    xbmc.executebuiltin('ActivateWindowAndFocus(%d,%d,%d)' % (window_id, control_id, index))
    log('opened window %d with focus at index %d' % (window_id, index))


def main():'''
t = t.replace('def main():', func, 1)

old_dispatch = '''    mode = arguments[0]
    control_id = as_int(arguments[1], -1) if len(arguments) > 1 else -1
    if mode == 'playlist':
        focus_playlist(control_id)'''
new_dispatch = '''    mode = arguments[0]
    first = as_int(arguments[1], -1) if len(arguments) > 1 else -1
    second = as_int(arguments[2], -1) if len(arguments) > 2 else -1
    if mode == 'open':
        open_playlist(first, second)
    elif mode == 'playlist':
        focus_playlist(first)'''
assert old_dispatch in t
t = t.replace(old_dispatch, new_dispatch, 1)
t = t.replace('''    elif mode == 'wall':
        focus_wall(control_id)''', '''    elif mode == 'wall':
        focus_wall(first)''', 1)
open(p, 'w', encoding='utf-8').write(t)
print('open mode added')

p = 'addon.xml'
t = open(p, encoding='utf-8').read()
t = t.replace('version="1.0.0"', 'version="1.0.1"', 1)
open(p, 'w', encoding='utf-8').write(t)
print('addon version -> 1.0.1')
