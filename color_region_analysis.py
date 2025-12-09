#!/usr/bin/env python3
"""
色領域の詳細解析 - RGB値周辺の構造を調べる
"""

import base64
import zlib
import xml.etree.ElementTree as ET
import struct


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


def hex_dump_region(data: bytes, start: int, length: int, label: str):
    """指定領域のhexダンプ"""
    print(f"\n{label} (0x{start:04X} - 0x{start+length:04X}):")
    for i in range(start, min(start + length, len(data)), 16):
        offset_str = f"0x{i:04X}"
        chunk = data[i:min(i+16, len(data))]
        hex_str = " ".join(f"{b:02X}" for b in chunk)
        hex_str = hex_str.ljust(47)
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)

        # RGB候補を強調表示
        markers = ""
        if i == 0x01AB or i == 0x01A0:  # 赤のRGB周辺
            markers = " <-- RGB候補(赤)"
        elif i == 0x01AD or i == 0x01A0:  # 青のRGB周辺
            markers = " <-- RGB候補(青)"

        print(f"{offset_str}  {hex_str}  |{ascii_str}|{markers}")


# ファイル読み込み
red = extract_binary("赤・ストローク無し.prtextstyle")
blue = extract_binary("青・ストローク無し.prtextstyle")

print("="*80)
print("Fill Color領域の詳細解析")
print("="*80)

# 赤のRGB (0x01AB: FF 00 00) 周辺
hex_dump_region(red, 0x0190, 80, "赤ファイル - RGB周辺")

# 青のRGB (0x01AD: 00 00 FF) 周辺
hex_dump_region(blue, 0x0190, 80, "青ファイル - RGB周辺")

# より広い範囲で比較
print("\n" + "="*80)
print("0x0180-0x01E0の範囲でバイト比較")
print("="*80)

for i in range(0x0180, min(0x01E0, min(len(red), len(blue)))):
    if red[i] != blue[i]:
        print(f"0x{i:04X}: 赤={red[i]:3d}(0x{red[i]:02X}) vs 青={blue[i]:3d}(0x{blue[i]:02X})  |  差分={abs(red[i]-blue[i]):3d}")

# RGB値の直前・直後のデータを詳細に見る
print("\n" + "="*80)
print("RGB値の前後16バイト")
print("="*80)

print("\n【赤ファイル】RGB位置: 0x01AB")
rgb_offset_red = 0x01AB
start_red = max(0, rgb_offset_red - 16)
end_red = min(len(red), rgb_offset_red + 16)

print(f"前16バイト (0x{start_red:04X} - 0x{rgb_offset_red:04X}):")
chunk_before = red[start_red:rgb_offset_red]
print("  Hex:", " ".join(f"{b:02X}" for b in chunk_before))
print("  Dec:", " ".join(f"{b:3d}" for b in chunk_before))

print(f"\nRGB (0x{rgb_offset_red:04X} - 0x{rgb_offset_red+3:04X}):")
rgb_chunk = red[rgb_offset_red:rgb_offset_red+3]
print("  Hex:", " ".join(f"{b:02X}" for b in rgb_chunk))
print("  Dec:", " ".join(f"{b:3d}" for b in rgb_chunk), "← (R, G, B) = (255, 0, 0)")

print(f"\n後16バイト (0x{rgb_offset_red+3:04X} - 0x{end_red:04X}):")
chunk_after = red[rgb_offset_red+3:end_red]
print("  Hex:", " ".join(f"{b:02X}" for b in chunk_after))
print("  Dec:", " ".join(f"{b:3d}" for b in chunk_after))

# 次のバイトがAlphaの可能性
if rgb_offset_red + 3 < len(red):
    alpha_candidate = red[rgb_offset_red + 3]
    print(f"\n  → 次のバイト(Alpha候補): {alpha_candidate} (0x{alpha_candidate:02X})")
    if alpha_candidate == 255:
        print("     = 255 → 完全不透明の可能性")

print("\n" + "-"*80)

print("\n【青ファイル】RGB位置: 0x01AD")
rgb_offset_blue = 0x01AD
start_blue = max(0, rgb_offset_blue - 16)
end_blue = min(len(blue), rgb_offset_blue + 16)

print(f"前16バイト (0x{start_blue:04X} - 0x{rgb_offset_blue:04X}):")
chunk_before = blue[start_blue:rgb_offset_blue]
print("  Hex:", " ".join(f"{b:02X}" for b in chunk_before))
print("  Dec:", " ".join(f"{b:3d}" for b in chunk_before))

print(f"\nRGB (0x{rgb_offset_blue:04X} - 0x{rgb_offset_blue+3:04X}):")
rgb_chunk = blue[rgb_offset_blue:rgb_offset_blue+3]
print("  Hex:", " ".join(f"{b:02X}" for b in rgb_chunk))
print("  Dec:", " ".join(f"{b:3d}" for b in rgb_chunk), "← (R, G, B) = (0, 0, 255)")

print(f"\n後16バイト (0x{rgb_offset_blue+3:04X} - 0x{end_blue:04X}):")
chunk_after = blue[rgb_offset_blue+3:end_blue]
print("  Hex:", " ".join(f"{b:02X}" for b in chunk_after))
print("  Dec:", " ".join(f"{b:3d}" for b in chunk_after))

if rgb_offset_blue + 3 < len(blue):
    alpha_candidate = blue[rgb_offset_blue + 3]
    print(f"\n  → 次のバイト(Alpha候補): {alpha_candidate} (0x{alpha_candidate:02X})")
    if alpha_candidate == 255:
        print("     = 255 → 完全不透明の可能性")

# RGBAとして4バイトを見る
print("\n" + "="*80)
print("RGBA (4バイト) として解析")
print("="*80)

print("\n赤ファイル:")
if rgb_offset_red + 4 <= len(red):
    rgba_red = red[rgb_offset_red:rgb_offset_red+4]
    r, g, b, a = rgba_red
    print(f"  0x{rgb_offset_red:04X}: {r:3d} {g:3d} {b:3d} {a:3d}  =  RGBA({r}, {g}, {b}, {a})")
    print(f"  Hex: {' '.join(f'{x:02X}' for x in rgba_red)}")

print("\n青ファイル:")
if rgb_offset_blue + 4 <= len(blue):
    rgba_blue = blue[rgb_offset_blue:rgb_offset_blue+4]
    r, g, b, a = rgba_blue
    print(f"  0x{rgb_offset_blue:04X}: {r:3d} {g:3d} {b:3d} {a:3d}  =  RGBA({r}, {g}, {b}, {a})")
    print(f"  Hex: {' '.join(f'{x:02X}' for x in rgba_blue)}")

# フォーマット推測
print("\n" + "="*80)
print("フォーマット推測")
print("="*80)
print("""
確定情報:
- Fill.SolidColor は RGB (3バイト) または RGBA (4バイト) で格納
- バイトオーダー: RGB（リトルエンディアンではない、そのまま）
- 値の範囲: 0-255 (uint8)
- 赤ファイル: R=255, G=0, B=0  → オフセット 0x01AB-0x01AD
- 青ファイル: R=0, G=0, B=255  → オフセット 0x01AD-0x01AF

注意: 赤と青でオフセットが2バイトずれている。
      → バイナリ構造がわずかに異なる（サイズ差: 赤480byte vs 青476byte = 4byte差）

推測:
- 直後のバイトがAlpha値の可能性
- 前後のデータは構造を示すヘッダやタグ
""")

print("\n次のステップ: グラデーション・Strokeファイルも同様に解析")
