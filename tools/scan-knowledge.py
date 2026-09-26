import re, glob

# Signatures actually observed in this batch's failures, not generic guessing.
CHECKS = [
    ('CJK/FFFD',        re.compile(r'[　-鿿�]')),
    # fused token: lowercase run directly followed by capitalised run
    ('fused-case',      re.compile(r'\b[a-z]{3,}[A-Z][a-z]{2,}\b')),
    # adjacent duplicate: "X, bukan sekadar X" / "yang Berf berlaku"
    # stray interpolation artefact: "meng{Prakata}tidak"
    ('stray-brace',     re.compile(r'\w\s*\{[^}]*\}\s*\w+')),
    # English function word inside Indonesian clause (not in a quote/table)
    ('en-infix',        re.compile(r'\b(?:dan|kang|dengan|untuk)\s+(?:the|and|with|from|that|this|are|was|were|have|has|been|not|which|these|those|serves|versus|will|would|should|could)\b')),
    # fragment typical of drift: "Kelemahanolversinya", "sertaibrate"
    ('tail-fragment',   re.compile(r'\b\w{2,}(?:olver|ibrate|drift|garbl)\w*\b', re.I)),
]

def scan(path):
    out = []
    for i, l in enumerate(open(path, encoding='utf-8'), 1):
        if l.lstrip().startswith(('|', '>', '-', '*', '#')) or '`' in l or 'http' in l:
            continue
        for name, rx in CHECKS:
            for m in rx.finditer(l):
                out.append((name, i, m.group(0)[:60], l.strip()[:90]))
    return out

files = sorted(glob.glob('knowledge/**/*.md', recursive=True))
total = 0
for f in files:
    h = scan(f)
    if not h:
        continue
    total += len(h)
    print(f'\n{f}  ({len(h)} hit(s))')
    seen = set()
    for name, i, what, ctx in h:
        k = (name, what)
        if k in seen:
            continue
        seen.add(k)
        print(f'   {name:14} L{i}: {what!r}')
        print(f'                   ...{ctx}')
print(f'\n=== {total} hit(s) across {len(files)} files ===')
