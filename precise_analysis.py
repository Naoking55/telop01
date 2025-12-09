#!/usr/bin/env python3
"""
精密解析 - 特定オフセットのfloat値を正確に確認
"""

import base64
import zlib
import xml.etree.ElementTree as ET
import struct
from pathlib import Path


def extract_binary(file_path: str) -> bytes:
    """バイナリ抽出"""
    tree = ET.parse(file_path)
    root = tree.getroot()
    for elem in root.iter():
        if elem.tag == 'StartKeyframeValue' and elem.get('Encoding') == 'base64':
            if elem.text:
                encoded = elem.text.strip()
                decoded = base64.b64decode(encoded)
                try:
                    return zlib.decompress(decoded)
                except:
                    return decoded
    return None


def read_float(data: bytes, offset: int) -> float:
    """Float32読み取り"""
    if offset + 4 <= len(data):
        return struct.unpack('<f', data[offset:offset+4])[0]
    return None


def read_hex(data: bytes, offset: int, length: int = 4) -> str:
    """Hex文字列取得"""
    chunk = data[offset:offset+length]
    return " ".join(f"{b:02X}" for b in chunk)


# ファイル読み込み
red = extract_binary("赤・ストローク無し.prtextstyle")
blue = extract_binary("青・ストローク無し.prtextstyle")

print("="*80)
print("赤 vs 青 の精密解析")
print("="*80)
print()

# Hex比較で見つかった興味深いオフセット
offsets_to_check = [
    (0x0180, "offset_0x0180"),
    (0x0184, "offset_0x0184"),
    (0x0188, "offset_0x0188"),
    (0x018C, "offset_0x018C"),
    (0x0190, "offset_0x0190"),
    (0x0194, "offset_0x0194"),
    (0x0198, "offset_0x0198"),
    (0x019C, "offset_0x019C"),
    (0x01A0, "offset_0x01A0"),
]

for offset, name in offsets_to_check:
    r_val = read_float(red, offset)
    b_val = read_float(blue, offset)
    r_hex = read_hex(red, offset)
    b_hex = read_hex(blue, offset)

    print(f"{name}:")
    print(f"  赤: {r_hex} = {r_val:.6f}")
    print(f"  青: {b_hex} = {b_val:.6f}")

    if r_val and b_val:
        # 0-1範囲のfloatならRGB値の可能性
        if 0 <= r_val <= 1 and 0 <= b_val <= 1:
            print(f"  → RGB値の可能性: {r_val*255:.1f}/255 vs {b_val*255:.1f}/255")
        elif r_val != b_val:
            print(f"  → 差分あり")
    print()

# さらに、赤と青の全バイトを比較して、連続した16バイト（RGBA x 4成分）の差分を探す
print("="*80)
print("連続16バイト（RGBA候補）の差分検出")
print("="*80)
print()

min_len = min(len(red), len(blue))
for i in range(0, min_len - 15, 4):  # 4バイトアライメント
    # 16バイト（4x float32）として読み取り
    red_vals = [read_float(red, i + j*4) for j in range(4)]
    blue_vals = [read_float(blue, i + j*4) for j in range(4)]

    # すべてがfloatとして有効で、0-1範囲にある
    if all(v is not None and 0 <= v <= 1 for v in red_vals + blue_vals):
        # かつ、差分がある
        if red_vals != blue_vals:
            r, g, b, a = red_vals
            r2, g2, b2, a2 = blue_vals

            print(f"オフセット 0x{i:04X}:")
            print(f"  赤: R={r:.4f}, G={g:.4f}, B={b:.4f}, A={a:.4f}")
            print(f"  青: R={r2:.4f}, G={g2:.4f}, B={b2:.4f}, A={a2:.4f}")
            print(f"  → 赤色値: ({int(r*255)}, {int(g*255)}, {int(b*255)})")
            print(f"  → 青色値: ({int(r2*255)}, {int(g2*255)}, {int(b2*255)})")
            print()

print("="*80)
print("FlatBuffer風のTLV構造を探索")
print("="*80)
print()

# FlatBufferやProtobufでは、フィールドはタグ（型+ID）とデータで構成される
# 色情報がどこにあるか、パターンを探す

# 赤ファイルで、値が 1.0 に近いfloat32を探す（赤なら R=1.0のはず）
print("赤ファイルで 0.8-1.0 範囲のfloat32:")
for i in range(len(red) - 3):
    val = read_float(red, i)
    if val and 0.8 <= val <= 1.0:
        hex_str = read_hex(red, i)
        print(f"  0x{i:04X}: {hex_str} = {val:.6f}")
        # 周辺も見る
        context = read_hex(red, max(0, i-8), 24)
        print(f"    コンテキスト: {context}")

print()

# 青ファイルで、値が 0.8-1.0 範囲のfloat32を探す（青なら B=1.0のはず）
print("青ファイルで 0.8-1.0 範囲のfloat32:")
for i in range(len(blue) - 3):
    val = read_float(blue, i)
    if val and 0.8 <= val <= 1.0:
        hex_str = read_hex(blue, i)
        print(f"  0x{i:04X}: {hex_str} = {val:.6f}")
        context = read_hex(blue, max(0, i-8), 24)
        print(f"    コンテキスト: {context}")
