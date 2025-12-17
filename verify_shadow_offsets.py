#!/usr/bin/env python3
"""
全スタイルでシャドウパラメータオフセットを検証
"""

import re
import base64
import struct
import json

# PRSL完全データを読み込み
with open('/tmp/prsl_complete_data.json', 'r') as f:
    prsl_data = json.load(f)

# prtextstyle読み込み
with open('/home/user/telop01/10styles/10styles.prtextstyle', 'r') as f:
    content = f.read()

pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
matches = re.findall(pattern, content, re.DOTALL)

print("="*80)
print("全スタイルのシャドウパラメータオフセット検証")
print("="*80)

for i in range(min(len(prsl_data), len(matches))):
    prsl = prsl_data[i]
    shadow = prsl.get('shadow', {})

    if not shadow.get('enabled'):
        continue

    # バイナリデコード
    b64_clean = matches[i].replace('\n', '').replace(' ', '').replace('\t', '')
    binary = base64.b64decode(b64_clean)

    print(f"\n{'='*80}")
    print(f"スタイル {i+1}: {prsl['name']}")
    print('='*80)

    print(f"PRSL値:")
    print(f"  ぼかし: {shadow['blur']}")
    print(f"  角度: {shadow['angle']}°")
    print(f"  距離: {shadow['distance']}")
    print(f"  色: RGBA({shadow['r']}, {shadow['g']}, {shadow['b']}, {shadow['a']})")
    print(f"  不透明度%: {shadow['a']/255.0*100:.1f}%")

    # バイナリから読み取り
    print(f"\nバイナリ値:")

    if len(binary) > 0x00a8 + 4:
        blur = struct.unpack('<f', binary[0x009c:0x00a0])[0]
        distance = struct.unpack('<f', binary[0x00a0:0x00a4])[0]
        angle_raw = struct.unpack('<f', binary[0x00a4:0x00a8])[0]
        alpha_pct = struct.unpack('<f', binary[0x00a8:0x00ac])[0]

        print(f"  0x009c ぼかし: {blur:.1f} {'✓' if abs(blur - shadow['blur']) < 0.1 else '✗'}")
        print(f"  0x00a0 距離: {distance:.1f} {'✓' if abs(distance - shadow['distance']) < 0.1 else '✗'}")
        print(f"  0x00a4 角度（生）: {angle_raw:.1f}°")
        print(f"  0x00a8 不透明度: {alpha_pct:.1f}% {'✓' if abs(alpha_pct - shadow['a']/255.0*100) < 0.1 else '✗'}")

        # 角度の変換を推測
        expected_angle = shadow['angle']
        # 様々な変換を試す
        if abs(angle_raw - expected_angle) < 0.1:
            print(f"    角度一致: そのまま ✓")
        elif abs(angle_raw - (expected_angle - 360)) < 0.1:
            print(f"    角度一致: angle - 360 ✓")
        elif abs(angle_raw + expected_angle) < 0.1:
            print(f"    角度一致: -angle ✓")
        elif abs(angle_raw - (expected_angle - 90)) < 0.1:
            print(f"    角度一致: angle - 90 ✓")
        else:
            # Premiere might use different angle origin (90° offset is common)
            adjusted = (expected_angle + 270) % 360 - 360 if expected_angle >= 90 else expected_angle + 270
            if abs(angle_raw - adjusted) < 0.1:
                print(f"    角度一致: (angle + 270) % 360 - 360 ✓")
            else:
                print(f"    角度不一致（期待={expected_angle}°, 実際={angle_raw}°）")

    # RGBバイトを探す
    r, g, b = shadow['r'], shadow['g'], shadow['b']
    print(f"\n  RGB [{r}, {g}, {b}] を探す:")
    for offset in range(len(binary) - 2):
        if (binary[offset] == r and
            binary[offset+1] == g and
            binary[offset+2] == b):
            print(f"    0x{offset:04x}: [{binary[offset]}, {binary[offset+1]}, {binary[offset+2]}] (次={binary[offset+3]})")

print(f"\n{'='*80}")
