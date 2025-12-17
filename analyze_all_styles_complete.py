#!/usr/bin/env python3
"""
10styles全体の完全解析
PRSLパラメータとprtextstyleバイナリの対応付け
"""

import re
import base64
import struct
import json

MARKER = b'\x02\x00\x00\x00\x41\x61'

# PRSL完全データを読み込み
with open('/tmp/prsl_complete_data.json', 'r') as f:
    prsl_data = json.load(f)

# prtextstyle読み込み
with open('/home/user/telop01/10styles/10styles.prtextstyle', 'r') as f:
    content = f.read()

pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
matches = re.findall(pattern, content, re.DOTALL)

print("="*80)
print("全スタイルのバイナリ解析（パラメータ位置特定）")
print("="*80)

results = []

for i in range(min(len(prsl_data), len(matches))):
    prsl = prsl_data[i]

    # バイナリデコード
    b64_clean = matches[i].replace('\n', '').replace(' ', '').replace('\t', '')
    binary = base64.b64decode(b64_clean)

    marker_pos = binary.find(MARKER)

    print(f"\n{'='*80}")
    print(f"スタイル {i+1}: {prsl['name']}")
    print('='*80)
    print(f"バイナリサイズ: {len(binary)} bytes")
    print(f"マーカー位置: 0x{marker_pos:04x}")

    # 塗り色バイトを確認
    fill = prsl['fill']
    expected_r, expected_g, expected_b = fill['r'], fill['g'], fill['b']

    # 色構造
    stored_components = []
    if expected_r != 255:
        stored_components.append(('R', expected_r))
    if expected_g != 255:
        stored_components.append(('G', expected_g))
    if expected_b != 255:
        stored_components.append(('B', expected_b))

    num_bytes = len(stored_components)
    if marker_pos >= num_bytes:
        actual_bytes = [binary[marker_pos - num_bytes + j] for j in range(num_bytes)]
        print(f"\n塗り色:")
        print(f"  期待: RGB({expected_r}, {expected_g}, {expected_b})")
        print(f"  保存成分数: {num_bytes}")
        print(f"  実際: {actual_bytes}")
        match = all(actual_bytes[j] == stored_components[j][1] for j in range(num_bytes))
        print(f"  一致: {'✓' if match else '✗'}")

    # シャドウぼかしを探す
    shadow = prsl['shadow']
    if shadow.get('enabled'):
        blur_expected = shadow['blur']
        print(f"\nシャドウぼかし:")
        print(f"  期待値: {blur_expected}")

        # Float値を探索
        for offset in range(0, len(binary) - 4, 4):
            try:
                val = struct.unpack('<f', binary[offset:offset+4])[0]
                if abs(val - blur_expected) < 0.1:
                    print(f"  検出: 0x{offset:04x} = {val:.1f} ✓")
                    break
            except:
                pass

    results.append({
        'index': i + 1,
        'size': len(binary),
        'marker_pos': marker_pos,
        'fill_bytes': num_bytes
    })

print(f"\n{'='*80}")
print("サマリー")
print('='*80)
print(f"{'Style':<8} {'サイズ':>8} {'マーカー':>8} {'塗りバイト':>10}")
print('-'*80)
for r in results:
    print(f"{r['index']:<8} {r['size']:>8} {r['marker_pos']:>8} {r['fill_bytes']:>10}")
