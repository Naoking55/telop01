#!/usr/bin/env python3
"""
シャドウ色マーカーの探索
塗り色と同様のマーカーパターンがあるかを調査
"""

import re
import base64
import json

# PRSL完全データを読み込み
with open('/tmp/prsl_complete_data.json', 'r') as f:
    prsl_data = json.load(f)

# prtextstyle読み込み
with open('/home/user/telop01/10styles/10styles.prtextstyle', 'r') as f:
    content = f.read()

pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
matches = re.findall(pattern, content, re.DOTALL)

# 塗り色のマーカー
FILL_MARKER = b'\x02\x00\x00\x00\x41\x61'

print("="*80)
print("シャドウ色エリアのマーカー探索")
print("="*80)

# Style 6を詳細分析（全パラメータが揃っている）
i = 5
prsl = prsl_data[i]

# バイナリデコード
b64_clean = matches[i].replace('\n', '').replace(' ', '').replace('\t', '')
binary = base64.b64decode(b64_clean)

shadow = prsl['shadow']
r, g, b, a = shadow['r'], shadow['g'], shadow['b'], shadow['a']

print(f"\nスタイル {i+1}: {prsl['name']}")
print(f"シャドウ色: RGBA({r}, {g}, {b}, {a})")
print(f"バイナリサイズ: {len(binary)} bytes")

# RGB[77, 68, 47]が見つかった0x00d9周辺を詳細ダンプ
print(f"\n0x00d9周辺の16進ダンプ:")
start = 0x00d0
for offset in range(start, min(start + 32, len(binary))):
    byte_val = binary[offset]
    hex_str = f'{byte_val:02x}'
    marker = ""

    if offset == 0x00d9:
        marker = " ← RGB[0] (R)"
    elif offset == 0x00da:
        marker = " ← RGB[1] (G)"
    elif offset == 0x00db:
        marker = " ← RGB[2] (B)"
    elif offset == 0x00dc:
        marker = " ← 次のバイト"

    print(f"  0x{offset:04x}: {hex_str} ({byte_val:3d}){marker}")

# シャドウ色の前後でパターンを探す
print(f"\n0x00d9前後のバイトパターン:")
if 0x00d9 >= 10:
    before_10 = binary[0x00d9-10:0x00d9]
    at_rgb = binary[0x00d9:0x00d9+3]
    after_3 = binary[0x00d9+3:0x00d9+6]

    print(f"  10バイト前: {' '.join(f'{b:02x}' for b in before_10)}")
    print(f"  RGB値:      {' '.join(f'{b:02x}' for b in at_rgb)} = [{r}, {g}, {b}]")
    print(f"  3バイト後:  {' '.join(f'{b:02x}' for b in after_3)}")

# 塗り色マーカーとの比較
fill_marker_pos = binary.find(FILL_MARKER)
print(f"\n塗り色マーカー位置: 0x{fill_marker_pos:04x}")
print(f"シャドウRGB位置: 0x00d9")
print(f"距離: {0x00d9 - fill_marker_pos} bytes")

# 他のスタイルも確認
print(f"\n{'='*80}")
print("他のスタイルのシャドウ色位置")
print('='*80)

for i in [4, 5, 7]:  # Styles 5, 6, 8 (varied colors)
    prsl = prsl_data[i]
    shadow = prsl.get('shadow', {})

    if not shadow.get('enabled'):
        continue

    b64_clean = matches[i].replace('\n', '').replace(' ', '').replace('\t', '')
    binary = base64.b64decode(b64_clean)

    r, g, b = shadow['r'], shadow['g'], shadow['b']

    print(f"\nスタイル {i+1}: RGB({r}, {g}, {b})")

    # RGBパターンを探す
    for offset in range(len(binary) - 2):
        if (binary[offset] == r and
            binary[offset+1] == g and
            binary[offset+2] == b):
            # 前後を表示
            if offset >= 4:
                before_4 = binary[offset-4:offset]
                after_1 = binary[offset+3] if offset+3 < len(binary) else 0
                print(f"  0x{offset:04x}: 前[{' '.join(f'{b:02x}' for b in before_4)}] RGB[{r:02x} {g:02x} {b:02x}] 次[{after_1:02x}]")
                break

print(f"\n{'='*80}")
