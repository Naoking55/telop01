#!/usr/bin/env python3
"""
青白赤グラデーションの全ストップをマッピング
0%, 30%, 100%の3つのストップを特定
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

def scan_for_positions(binary):
    """グラデーションストップ位置をスキャン"""
    positions = []

    for offset in range(0, len(binary) - 3, 4):
        try:
            val = struct.unpack('<f', binary[offset:offset+4])[0]

            # 0.0, 0.3, 1.0に近い値を探す
            if abs(val - 0.0) < 0.01 or abs(val - 0.3) < 0.01 or abs(val - 1.0) < 0.01:
                # 直後にalpha値（0.5）があるか確認
                if offset + 8 <= len(binary):
                    alpha = struct.unpack('<f', binary[offset+4:offset+8])[0]
                    if abs(alpha - 0.5) < 0.01:
                        positions.append((offset, val, alpha))
        except:
            pass

    return positions

def find_rgb_near_offset(binary, base_offset, search_range=32):
    """指定オフセット周辺でRGB bytesを探す"""
    colors_found = []

    start = max(0, base_offset - search_range)
    end = min(len(binary), base_offset + search_range)

    for offset in range(start, end - 2):
        r, g, b = binary[offset:offset+3]

        color_name = ''
        if r == 255 and g == 255 and b == 255:
            color_name = '白'
        elif r == 255 and g == 0 and b == 0:
            color_name = '赤'
        elif r == 0 and g == 0 and b == 255:
            color_name = '青'

        if color_name:
            distance = offset - base_offset
            colors_found.append((color_name, offset, r, g, b, distance))

    return colors_found

def main():
    files = glob.glob('prtextstyle/*青白赤*30.prtextstyle')
    file = files[0]

    print("="*80)
    print("青白赤グラデーションの完全マッピング")
    print("="*80)
    print(f"\nFile: {file}\n")

    binary = get_binary_from_prtextstyle(file)

    if not binary:
        print("❌ バイナリ取得失敗")
        return

    print(f"バイナリサイズ: {len(binary)} bytes\n")

    # グラデーションストップ位置をスキャン
    positions = scan_for_positions(binary)

    print("="*80)
    print(f"検出されたグラデーションストップ: {len(positions)} 箇所")
    print("="*80)
    print()

    # 各ストップの詳細
    for i, (offset, position, alpha) in enumerate(sorted(positions, key=lambda x: x[1]), 1):
        print(f"ストップ {i}:")
        print(f"  位置オフセット: 0x{offset:04x}")
        print(f"  Position値: {position:.2f} ({position*100:.0f}%)")
        print(f"  Alpha値: {alpha:.2f}")

        # 周辺の色を探す
        colors = find_rgb_near_offset(binary, offset, search_range=32)

        if colors:
            print(f"  周辺の色:")
            for color_name, color_offset, r, g, b, distance in colors:
                print(f"    {color_name} @ 0x{color_offset:04x}: RGB({r:3d}, {g:3d}, {b:3d}) (距離: {distance:+3d} bytes)")
        else:
            print(f"  周辺に色データなし")

        print()

    # グラデーション構造の推定
    print("="*80)
    print("グラデーション構造の推定:")
    print("="*80)
    print()

    if len(positions) >= 3:
        # 位置でソート
        sorted_positions = sorted(positions, key=lambda x: x[1])

        print("想定される構造:")
        print(f"  0%ストップ   (青): 0x{sorted_positions[0][0]:04x}")
        print(f" 30%ストップ   (白): 0x{sorted_positions[1][0]:04x}")
        print(f"100%ストップ   (赤): 0x{sorted_positions[2][0]:04x}")
        print()

        # 各ストップのデータサイズを推定
        if len(sorted_positions) >= 2:
            size_1_2 = sorted_positions[1][0] - sorted_positions[0][0]
            size_2_3 = sorted_positions[2][0] - sorted_positions[1][0]

            print(f"ストップ間の距離:")
            print(f"  0% → 30%: {size_1_2} bytes")
            print(f"  30% → 100%: {size_2_3} bytes")
            print()

            print(f"平均ストップサイズ: {(size_1_2 + size_2_3) // 2} bytes")

if __name__ == "__main__":
    main()
