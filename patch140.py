import re
p = 'service.py'
t = open(p, encoding='utf-8').read()

helper = '''
def _png_rows(head):
    """Decode a small 8-bit non-interlaced PNG into (width, height, bpp, rows)."""
    import zlib
    if head[:8] != b'\\x89PNG\\r\\n\\x1a\\n':
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


def main():'''

t = t.replace('def main():', helper, 1)

t = t.replace("""    if head[:8] == b'\\x89PNG\\r\\n\\x1a\\n':
        return png_has_alpha(head)""",
"""    if head[:8] == b'\\x89PNG\\r\\n\\x1a\\n':
        if not png_has_alpha(head):
            return False
        return not bool(_opaque_black_edges(head))""", 1)

t = t.replace("""    try:
        with open(source, 'rb') as handle:
            head = handle.read(HEAD_BYTES)""",
"""    try:
        with open(source, 'rb') as handle:
            head = handle.read()""", 1)
t = t.replace("""        with urllib.request.urlopen(request, timeout=4) as response:
            head = response.read(HEAD_BYTES)""",
"""        with urllib.request.urlopen(request, timeout=6) as response:
            head = response.read()""", 1)

open(p, 'w', encoding='utf-8').write(t)
print('service.py: pixel-level matte detection added')

p = 'addon.xml'
t = open(p, encoding='utf-8').read()
t = t.replace('version="1.3.0"', 'version="1.4.0"', 1)
open(p, 'w', encoding='utf-8').write(t)
print('addon -> 1.4.0')
