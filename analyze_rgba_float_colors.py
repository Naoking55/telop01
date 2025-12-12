#!/usr/bin/env python3
"""
RGBA float形式の色データを検索
グラデーションではRGBA floatが使われている可能性を調査
"""

import glob
import xml.etree.ElementTree as ET
import base64
import struct

def get_binary_from_prtextstyle(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()

    for arb_param in root.findall('.//ArbVideoComponentParam'):
        name_elem = arb_param.find('.//Name')
        if name_elem is not None and ('Source Text' in name_elem.text or 'ソーステキスト' in name_elem.text):
            binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
            if binary_elem is not None and binary_elem.text:
                return base64.b64decode(binary_elem.text.strip())
    return None

def find_rgba_float_colors(binary):
    """RGBA float形式の色を検索（各値0.0-1.0）"""
    colors = []

    for offset in range(0, len(binary) - 15, 4):
        try:
            r = struct.unpack('<f', binary[offset:offset+4])[0]
            g = struct.unpack('<f', binary[offset+4:offset+8])[0]
            b = struct.unpack('<f', binary[offset+8:offset+12])[0]
            a = struct.unpack('<f', binary[offset+12:offset+16])[0]

            # 全て0.0-1.0の範囲内か
            if all(-0.1 <= v <= 1.1 for v in [r, g, b, a]):
                # 特徴的な色を検出
                color_name = ''

                # 青: B=1.0, R=0, G=0
                if abs(b - 1.0) < 0.1 and abs(r) < 0.1 and abs(g) < 0.1:
                    color_name = '青 (Blue)'
                # 白: R=G=B=1.0
                elif abs(r - 1.0) < 0.1 and abs(g - 1.0) < 0.1 and abs(b - 1.0) < 0.1:
                    color_name = '白 (White)'
                # 赤: R=1.0, G=0, B=0
                elif abs(r - 1.0) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1:
                    color_name = '赤 (Red)'
                # 黒: R=G=B=0
                elif abs(r) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1:
                    color_name = '黒 (Black)'

                if color_name:
                    r255 = int(r * 255)
                    g255 = int(g * 255)
                    b255 = int(b * 255)
                    a255 = int(a * 255)
                    colors.append((offset, r, g, b, a, r255, g255, b255, a255, color_name))
        except:
            pass

    return colors

def hex_dump_area(binary, offset, before=16, after=16):
    """指定オフセット周辺の16進ダンプ"""
    start = max(0, offset - before)
    end = min(len(binary), offset + after)

    for i in range(start, end, 16):
        hex_parts = []
        for j in range(16):
            if i + j < end:
                byte = binary[i + j]
                # オフセット位置をハイライト（16バイト = RGBA 4つ分）
                if offset <= i + j < offset + 16:
                    hex_parts.append(f"\033[93m{byte:02x}\033[0m")  # 黄色
                else:
                    hex_parts.append(f"{byte:02x}")
            else:
                hex_parts.append("  ")

        hex_str = " ".join(hex_parts[:8]) + "  " + " ".join(hex_parts[8:])
        print(f"  {i:04x}  {hex_str}")

def main():
    files = glob.glob('prtextstyle/*青白赤*30.prtextstyle')
    if not files:
        print("❌ 青白赤グラデーションファイルが見つかりません")
        return

    file = files[0]

    print("="*80)
    print("RGBA Float形式の色データ検索")
    print("="*80)
    print(f"\nFile: {file}\n")

    binary = get_binary_from_prtextstyle(file)

    if not binary:
        print("❌ バイナリ取得失敗")
        return

    print(f"バイナリサイズ: {len(binary)} bytes\n")

    # RGBA float色を検出
    rgba_colors = find_rgba_float_colors(binary)

    print("="*80)
    print(f"検出されたRGBA Float色: {len(rgba_colors)} 箇所")
    print("="*80)
    print()

    # 色ごとにグループ化
    color_groups = {'青 (Blue)': [], '白 (White)': [], '赤 (Red)': [], '黒 (Black)': []}
    for color_data in rgba_colors:
        offset, r, g, b, a, r255, g255, b255, a255, color_name = color_data
        if color_name in color_groups:
            color_groups[color_name].append(color_data)

    for color_name, colors in color_groups.items():
        print(f"\n{color_name}: {len(colors)} 箇所")
        print("-" * 80)

        for offset, r, g, b, a, r255, g255, b255, a255, _ in colors:
            print(f"\n0x{offset:04x}: RGBA({r:.4f}, {g:.4f}, {b:.4f}, {a:.4f})")
            print(f"        = RGB({r255:3d}, {g255:3d}, {b255:3d}, {a255:3d})")

            # 16進ダンプ
            hex_dump_area(binary, offset, before=24, after=24)

    # グラデーションストップとの関係を調査
    print("\n" + "="*80)
    print("グラデーションストップとの位置関係")
    print("="*80)
    print()

    # 既知のストップ位置
    known_stops = [
        (0x019c, 1.0, "100%"),
        (0x01b0, 0.0, "0%"),
        (0x01d8, 1.0, "100%"),
        (0x0208, 0.3, "30%"),
        (0x0224, 0.0, "0%"),
    ]

    print("各ストップの近くのRGBA Float色:")
    print()

    for stop_offset, position, label in sorted(known_stops, key=lambda x: x[1]):
        print(f"{label} ストップ @ 0x{stop_offset:04x}:")

        nearby = []
        for offset, r, g, b, a, r255, g255, b255, a255, color_name in rgba_colors:
            distance = offset - stop_offset
            if -80 <= distance <= 80:
                nearby.append((distance, offset, color_name, r, g, b, a))

        if nearby:
            for distance, offset, color_name, r, g, b, a in sorted(nearby, key=lambda x: abs(x[0])):
                print(f"  {color_name:15s} @ 0x{offset:04x} (距離: {distance:+4d} bytes)")
                print(f"    RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f})")
        else:
            print("  近くにRGBA Float色なし")

        print()

    # RGB bytes形式の青色（0x0279）との関係
    print("\n" + "="*80)
    print("RGB bytes形式の青色（0x0279）との関係")
    print("="*80)
    print()

    blue_byte_offset = 0x0279
    print(f"青色 RGB bytes @ 0x{blue_byte_offset:04x}")
    print()

    print("近くのRGBA Float色:")
    for offset, r, g, b, a, r255, g255, b255, a255, color_name in rgba_colors:
        distance = offset - blue_byte_offset
        if -80 <= distance <= 80:
            print(f"  {color_name:15s} @ 0x{offset:04x} (距離: {distance:+4d} bytes)")
            print(f"    RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f})")

if __name__ == "__main__":
    main()
