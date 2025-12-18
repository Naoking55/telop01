#!/usr/bin/env python3
"""
グラデーション色のバイナリ位置を探索
スタイル8と10（グラデーション）を解析
"""

import re
import base64

# prtextstyle読み込み
with open('/home/user/telop01/10styles/10styles.prsl', 'rb') as f:
    content = f.read()

with open('/home/user/telop01/10styles/10styles.prtextstyle', 'r') as f:
    prt_content = f.read()

pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
matches = re.findall(pattern, prt_content, re.DOTALL)

# スタイル8（index 7）のグラデーション
print("="*80)
print("スタイル8（満天青空レストラン）")
print("="*80)
print("グラデーション: RGB(253,255,0) → RGB(188,163,0)")

b64_clean = matches[7].replace('\n', '').replace(' ', '').replace('\t', '')
binary = base64.b64decode(b64_clean)

print(f"バイナリサイズ: {len(binary)} bytes")

# 開始色 RGB(253, 255, 0) を探す
print(f"\n開始色 RGB(253, 255, 0) を探す:")
for offset in range(len(binary) - 2):
    if (binary[offset] == 253 and
        binary[offset+1] == 255 and
        binary[offset+2] == 0):
        # 前後を表示
        start = max(0, offset - 4)
        end = min(len(binary), offset + 7)
        context = ' '.join(f'{binary[i]:02x}' for i in range(start, end))
        marker = ' ' * ((offset - start) * 3) + '^^^ ^^^ ^^^'
        print(f"  0x{offset:04x}: {context}")
        print(f"         {marker}")

# 終了色 RGB(188, 163, 0) を探す
print(f"\n終了色 RGB(188, 163, 0) を探す:")
for offset in range(len(binary) - 2):
    if (binary[offset] == 188 and
        binary[offset+1] == 163 and
        binary[offset+2] == 0):
        # 前後を表示
        start = max(0, offset - 4)
        end = min(len(binary), offset + 7)
        context = ' '.join(f'{binary[i]:02x}' for i in range(start, end))
        marker = ' ' * ((offset - start) * 3) + '^^^ ^^^ ^^^'
        print(f"  0x{offset:04x}: {context}")
        print(f"         {marker}")

# 塗り色マーカーの位置も確認
FILL_MARKER = b'\x02\x00\x00\x00\x41\x61'
marker_pos = binary.find(FILL_MARKER)
print(f"\n塗り色マーカー位置: 0x{marker_pos:04x}")

# マーカー周辺を表示
if marker_pos > 0:
    start = max(0, marker_pos - 20)
    print(f"\nマーカー周辺（0x{start:04x} - 0x{marker_pos+10:04x}）:")
    for i in range(start, min(len(binary), marker_pos + 10)):
        hex_val = f'{binary[i]:02x}'
        if i == marker_pos:
            print(f"  0x{i:04x}: {hex_val} ← マーカー開始")
        elif marker_pos <= i < marker_pos + 6:
            print(f"  0x{i:04x}: {hex_val}   (マーカー)")
        else:
            print(f"  0x{i:04x}: {hex_val}")

print(f"\n{'='*80}")
print("スタイル10（A-OTF 新ゴ Pro U 145）")
print("="*80)
print("グラデーション: RGB(255,244,161) → RGB(255,223,0)")

b64_clean = matches[9].replace('\n', '').replace(' ', '').replace('\t', '')
binary = base64.b64decode(b64_clean)

print(f"バイナリサイズ: {len(binary)} bytes")

# 開始色 RGB(255, 244, 161) を探す
print(f"\n開始色 RGB(255, 244, 161) を探す:")
for offset in range(len(binary) - 2):
    if (binary[offset] == 255 and
        binary[offset+1] == 244 and
        binary[offset+2] == 161):
        # 前後を表示
        start = max(0, offset - 4)
        end = min(len(binary), offset + 7)
        context = ' '.join(f'{binary[i]:02x}' for i in range(start, end))
        marker = ' ' * ((offset - start) * 3) + '^^^ ^^^ ^^^'
        print(f"  0x{offset:04x}: {context}")
        print(f"         {marker}")

# 終了色 RGB(255, 223, 0) を探す
print(f"\n終了色 RGB(255, 223, 0) を探す:")
for offset in range(len(binary) - 2):
    if (binary[offset] == 255 and
        binary[offset+1] == 223 and
        binary[offset+2] == 0):
        # 前後を表示
        start = max(0, offset - 4)
        end = min(len(binary), offset + 7)
        context = ' '.join(f'{binary[i]:02x}' for i in range(start, end))
        marker = ' ' * ((offset - start) * 3) + '^^^ ^^^ ^^^'
        print(f"  0x{offset:04x}: {context}")
        print(f"         {marker}")

# マーカー
marker_pos = binary.find(FILL_MARKER)
print(f"\n塗り色マーカー位置: 0x{marker_pos:04x}")

print(f"\n{'='*80}")
