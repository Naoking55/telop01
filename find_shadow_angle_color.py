#!/usr/bin/env python3
"""
シャドウ角度と色の詳細探索
角度：度数法/ラジアン両方試す
色：Float形式（0.0-1.0）も試す
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
print("シャドウ角度と色の詳細探索")
print("="*80)

# Style 6を詳細分析
i = 5
prsl = prsl_data[i]

# バイナリデコード
b64_clean = matches[i].replace('\n', '').replace(' ', '').replace('\t', '')
binary = base64.b64decode(b64_clean)

print(f"\nスタイル {i+1}: {prsl['name']}")
print(f"バイナリサイズ: {len(binary)} bytes")

shadow = prsl['shadow']
print(f"\nシャドウパラメータ:")
print(f"  ぼかし: {shadow['blur']}")
print(f"  角度: {shadow['angle']}°")
print(f"  距離: {shadow['distance']}")
print(f"  色: RGBA({shadow['r']}, {shadow['g']}, {shadow['b']}, {shadow['a']})")

# 角度をラジアンに変換
angle_deg = shadow['angle']
angle_rad = math.radians(angle_deg)
print(f"\n角度変換:")
print(f"  度: {angle_deg}")
print(f"  ラジアン: {angle_rad}")

# ラジアン値を探す
print(f"\nラジアン値 {angle_rad:.6f} を探す:")
for offset in range(0, len(binary) - 4, 4):
    try:
        val = struct.unpack('<f', binary[offset:offset+4])[0]
        if abs(val - angle_rad) < 0.01:
            print(f"  0x{offset:04x} = {val:.6f} ✓")
    except:
        pass

# 度数法も念のため
print(f"\n度数法 {angle_deg} を探す:")
for offset in range(0, len(binary) - 4, 4):
    try:
        val = struct.unpack('<f', binary[offset:offset+4])[0]
        if abs(val - angle_deg) < 0.1:
            print(f"  0x{offset:04x} = {val:.1f} ✓")
    except:
        pass

# 色：Float形式（0.0-1.0）
r_float = shadow['r'] / 255.0
g_float = shadow['g'] / 255.0
b_float = shadow['b'] / 255.0
a_float = shadow['a'] / 255.0

print(f"\n色（Float形式）:")
print(f"  R: {r_float:.6f}")
print(f"  G: {g_float:.6f}")
print(f"  B: {b_float:.6f}")
print(f"  A: {a_float:.6f}")

# Float値を探す
for comp_name, comp_val in [('R', r_float), ('G', g_float), ('B', b_float), ('A', a_float)]:
    print(f"\n{comp_name}={comp_val:.6f} を探す:")
    found = False
    for offset in range(0, len(binary) - 4, 4):
        try:
            val = struct.unpack('<f', binary[offset:offset+4])[0]
            if abs(val - comp_val) < 0.001:
                print(f"  0x{offset:04x} = {val:.6f} ✓")
                found = True
        except:
            pass
    if not found:
        print(f"  見つかりませんでした")

# Byte形式の色も探す
print(f"\n色（Byte形式）: [{shadow['r']}, {shadow['g']}, {shadow['b']}, {shadow['a']}]")
print(f"連続するRGBAバイトパターンを探す:")
found_any = False
for offset in range(len(binary) - 3):
    if (binary[offset] == shadow['r'] and
        binary[offset+1] == shadow['g'] and
        binary[offset+2] == shadow['b'] and
        binary[offset+3] == shadow['a']):
        print(f"  0x{offset:04x}: [{binary[offset]}, {binary[offset+1]}, {binary[offset+2]}, {binary[offset+3]}] ✓")
        found_any = True

# RGB、RGBのみ、BGRAなど他のパターンも試す
if not found_any:
    print(f"\n他のパターンを探す:")
    # BGRA
    print(f"  BGRAパターン [{shadow['b']}, {shadow['g']}, {shadow['r']}, {shadow['a']}]:")
    for offset in range(len(binary) - 3):
        if (binary[offset] == shadow['b'] and
            binary[offset+1] == shadow['g'] and
            binary[offset+2] == shadow['r'] and
            binary[offset+3] == shadow['a']):
            print(f"    0x{offset:04x}: BGRA ✓")

    # RGB only
    print(f"  RGBパターン [{shadow['r']}, {shadow['g']}, {shadow['b']}]:")
    for offset in range(len(binary) - 2):
        if (binary[offset] == shadow['r'] and
            binary[offset+1] == shadow['g'] and
            binary[offset+2] == shadow['b']):
            print(f"    0x{offset:04x}: RGB (次のバイト={binary[offset+3]})")

# 0x009c周辺を16進ダンプ
print(f"\n0x009c周辺の16進ダンプ（シャドウパラメータエリア）:")
start = 0x009c
for offset in range(start, min(start + 48, len(binary)), 4):
    try:
        f_val = struct.unpack('<f', binary[offset:offset+4])[0]
        hex_bytes = ' '.join(f'{b:02x}' for b in binary[offset:offset+4])
        print(f"  0x{offset:04x}: {hex_bytes} = {f_val:.6f}")
    except:
        pass

print(f"\n{'='*80}")
