#!/usr/bin/env python3
"""
バイトパターン検索 - RGB値をbyte形式で探す
赤=(255,0,0) 青=(0,0,255) のパターンを探索
"""

import base64
import zlib
import xml.etree.ElementTree as ET
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


def find_byte_pattern(data: bytes, pattern: list, name: str):
    """特定のバイトパターンを検索"""
    print(f"\n{name}のパターン {pattern} を検索:")
    matches = []

    for i in range(len(data) - len(pattern) + 1):
        if list(data[i:i+len(pattern)]) == pattern:
            matches.append(i)
            # コンテキスト表示
            start = max(0, i - 16)
            end = min(len(data), i + len(pattern) + 16)
            context = data[start:end]
            hex_str = " ".join(f"{b:02X}" for b in context)
            print(f"  0x{i:04X}: {hex_str}")

    if not matches:
        print("  見つかりませんでした")

    return matches


def find_ff_patterns(data: bytes, name: str):
    """0xFF (255) を含むパターンを探す"""
    print(f"\n{name}で 0xFF を含む4バイトパターン:")

    for i in range(len(data) - 3):
        chunk = data[i:i+4]
        if 0xFF in chunk:
            # RGBAやBGRAのパターンとして意味がありそうか
            hex_str = " ".join(f"{b:02X}" for b in chunk)
            # 少なくとも1つのFFと1つの00がある（色として妥当）
            if chunk.count(0xFF) >= 1 and chunk.count(0x00) >= 1:
                print(f"  0x{i:04X}: {hex_str} = {list(chunk)}")


# ファイル読み込み
red = extract_binary("赤・ストローク無し.prtextstyle")
blue = extract_binary("青・ストローク無し.prtextstyle")

print("="*80)
print("バイトパターン検索: 赤 vs 青")
print("="*80)

# 赤色のパターン候補
# RGB: (255, 0, 0)
# RGBA: (255, 0, 0, 255)
# BGRA: (0, 0, 255, 255)
# ARGB: (255, 255, 0, 0)

print("\n【赤ファイル】")
find_byte_pattern(red, [255, 0, 0], "RGB(255,0,0)")
find_byte_pattern(red, [255, 0, 0, 255], "RGBA(255,0,0,255)")
find_byte_pattern(red, [0, 0, 255, 255], "BGRA(0,0,255,255)")
find_byte_pattern(red, [255, 255, 0, 0], "ARGB(255,255,0,0)")

# より柔軟な検索：FF と 00 の組み合わせ
find_ff_patterns(red, "赤")

print("\n" + "="*80)
print("\n【青ファイル】")
find_byte_pattern(blue, [0, 0, 255], "RGB(0,0,255)")
find_byte_pattern(blue, [0, 0, 255, 255], "RGBA(0,0,255,255)")
find_byte_pattern(blue, [255, 0, 0, 255], "BGRA(255,0,0,255)")
find_byte_pattern(blue, [255, 0, 0, 255], "ARGB(255,0,0,255)")

find_ff_patterns(blue, "青")

# 差分バイトの分析
print("\n" + "="*80)
print("差分バイト分析")
print("="*80)

min_len = min(len(red), len(blue))
diffs = []
for i in range(min_len):
    if red[i] != blue[i]:
        diffs.append((i, red[i], blue[i]))

print(f"\n差分バイト数: {len(diffs)}")
print("\n最初の50個の差分:")
for i, (offset, r_byte, b_byte) in enumerate(diffs[:50]):
    print(f"  0x{offset:04X}: 赤={r_byte:3d}(0x{r_byte:02X}), 青={b_byte:3d}(0x{b_byte:02X})")

# 255や0を含む差分に注目
print("\n0または255を含む差分:")
for offset, r_byte, b_byte in diffs:
    if r_byte == 255 or b_byte == 255 or r_byte == 0 or b_byte == 0:
        if r_byte != b_byte:  # 実際に異なる
            print(f"  0x{offset:04X}: 赤={r_byte:3d}, 青={b_byte:3d}")

# バイナリ全体をダンプ（最後の100バイト）
print("\n" + "="*80)
print("ファイル末尾の比較")
print("="*80)

print("\n赤ファイル（最後の64バイト）:")
for i in range(max(0, len(red) - 64), len(red), 16):
    chunk = red[i:min(i+16, len(red))]
    hex_str = " ".join(f"{b:02X}" for b in chunk)
    print(f"  0x{i:04X}: {hex_str}")

print("\n青ファイル（最後の64バイト）:")
for i in range(max(0, len(blue) - 64), len(blue), 16):
    chunk = blue[i:min(i+16, len(blue))]
    hex_str = " ".join(f"{b:02X}" for b in chunk)
    print(f"  0x{i:04X}: {hex_str}")
