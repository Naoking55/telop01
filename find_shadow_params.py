#!/usr/bin/env python3
"""
シャドウパラメータ位置の特定
オフセット（角度・距離）と色（RGBA）の保存位置を探す
"""

import re
import base64
import struct
import json
import math

# PRSL完全データを読み込み
with open('/tmp/prsl_complete_data.json', 'r') as f:
    prsl_data = json.load(f)

# prtextstyle読み込み
with open('/home/user/telop01/10styles/10styles.prtextstyle', 'r') as f:
    content = f.read()

pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
matches = re.findall(pattern, content, re.DOTALL)

print("="*80)
print("シャドウパラメータ位置の探索")
print("="*80)

# 異なるシャドウパラメータを持つスタイルを比較
# Style 5: angle=274°, distance=7, color RGB(0,0,0,147)
# Style 6: angle=326°, distance=4.5, color RGB(77,68,47,153)

for i in [4, 5]:  # Styles 5 and 6 (0-indexed)
    prsl = prsl_data[i]

    # バイナリデコード
    b64_clean = matches[i].replace('\n', '').replace(' ', '').replace('\t', '')
    binary = base64.b64decode(b64_clean)

    print(f"\n{'='*80}")
    print(f"スタイル {i+1}: {prsl['name']}")
    print('='*80)
    print(f"バイナリサイズ: {len(binary)} bytes")

    shadow = prsl['shadow']
    if shadow.get('enabled'):
        print(f"\nシャドウパラメータ（PRSL）:")
        print(f"  ぼかし: {shadow['blur']}")
        print(f"  角度: {shadow['angle']}°")
        print(f"  距離: {shadow['distance']}")
        print(f"  色: RGBA({shadow['r']}, {shadow['g']}, {shadow['b']}, {shadow['a']})")

        # Float値を探索
        print(f"\nFloat値の探索:")

        # ぼかし値
        blur_val = shadow['blur']
        print(f"\n  ぼかし={blur_val}を探す:")
        for offset in range(0, len(binary) - 4, 4):
            try:
                val = struct.unpack('<f', binary[offset:offset+4])[0]
                if abs(val - blur_val) < 0.1:
                    print(f"    0x{offset:04x} = {val:.1f} ✓")
            except:
                pass

        # 角度
        angle_val = shadow['angle']
        print(f"\n  角度={angle_val}°を探す:")
        for offset in range(0, len(binary) - 4, 4):
            try:
                val = struct.unpack('<f', binary[offset:offset+4])[0]
                if abs(val - angle_val) < 0.1:
                    print(f"    0x{offset:04x} = {val:.1f} ✓")
            except:
                pass

        # 距離
        dist_val = shadow['distance']
        print(f"\n  距離={dist_val}を探す:")
        for offset in range(0, len(binary) - 4, 4):
            try:
                val = struct.unpack('<f', binary[offset:offset+4])[0]
                if abs(val - dist_val) < 0.1:
                    print(f"    0x{offset:04x} = {val:.1f} ✓")
            except:
                pass

        # 色のバイト値を探す
        r, g, b, a = shadow['r'], shadow['g'], shadow['b'], shadow['a']
        print(f"\n  色バイト [{r}, {g}, {b}, {a}] を探す:")

        # RGBAの連続パターンを探す
        for offset in range(len(binary) - 3):
            if (binary[offset] == r and
                binary[offset+1] == g and
                binary[offset+2] == b and
                binary[offset+3] == a):
                print(f"    0x{offset:04x}: [{binary[offset]}, {binary[offset+1]}, {binary[offset+2]}, {binary[offset+3]}] ✓")

print(f"\n{'='*80}")
