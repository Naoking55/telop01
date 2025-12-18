#!/usr/bin/env python3
"""
青白赤グラデーションの完全な構造解析
全ての色データ（青・白・赤）を特定し、グラデーションストップとの関係を解明
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

def find_all_rgb_colors(binary):
    """全てのRGB色を検出（バイト形式）"""
    colors = []

    for offset in range(0, len(binary) - 2):
        r, g, b = binary[offset:offset+3]

        # 純色または特徴的な色を検出
        color_name = ''
        if r == 255 and g == 255 and b == 255:
            color_name = '白 (White)'
        elif r == 255 and g == 0 and b == 0:
            color_name = '赤 (Red)'
        elif r == 0 and g == 0 and b == 255:
            color_name = '青 (Blue)'
        elif r == 0 and g == 0 and b == 0:
            color_name = '黒 (Black)'

        if color_name:
            # 周辺のコンテキストを取得
            context_before = binary[max(0, offset-8):offset].hex()
            context_after = binary[offset+3:min(len(binary), offset+11)].hex()
            colors.append((offset, r, g, b, color_name, context_before, context_after))

    return colors

def find_all_float_values(binary, min_val=0.0, max_val=1.0):
    """全ての有効なfloat値を検出"""
    floats = []

    for offset in range(0, len(binary) - 3, 4):
        try:
            val = struct.unpack('<f', binary[offset:offset+4])[0]
            if min_val <= val <= max_val:
                floats.append((offset, val))
        except:
            pass

    return floats

def find_gradient_stops(binary):
    """グラデーションストップ（Position + Alpha のペア）を検出"""
    stops = []

    for offset in range(0, len(binary) - 7, 4):
        try:
            position = struct.unpack('<f', binary[offset:offset+4])[0]
            alpha = struct.unpack('<f', binary[offset+4:offset+8])[0]

            # 0.0-1.0の範囲のposition値
            if 0.0 <= position <= 1.0:
                # alpha値が0.3-1.0の範囲（0.5が典型的）
                if 0.3 <= alpha <= 1.0:
                    stops.append((offset, position, alpha))
        except:
            pass

    return stops

def hex_dump_area(binary, offset, before=16, after=16):
    """指定オフセット周辺の16進ダンプ"""
    start = max(0, offset - before)
    end = min(len(binary), offset + after)

    for i in range(start, end, 16):
        hex_parts = []
        for j in range(16):
            if i + j < end:
                byte = binary[i + j]
                # オフセット位置をハイライト
                if offset <= i + j < offset + 3:
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
    print("青白赤グラデーションの完全構造解析")
    print("="*80)
    print(f"\nFile: {file}\n")

    binary = get_binary_from_prtextstyle(file)

    if not binary:
        print("❌ バイナリ取得失敗")
        return

    print(f"バイナリサイズ: {len(binary)} bytes\n")

    # 1. 全RGB色を検出
    print("="*80)
    print("1. RGB色の完全リスト（バイト形式）")
    print("="*80)
    print()

    colors = find_all_rgb_colors(binary)

    for offset, r, g, b, name, ctx_before, ctx_after in colors:
        print(f"0x{offset:04x}: RGB({r:3d}, {g:3d}, {b:3d}) - {name}")
        print(f"  前: {ctx_before}")
        print(f"  後: {ctx_after}")
        print()

    # 2. グラデーションストップを検出
    print("="*80)
    print("2. グラデーションストップ（Position + Alpha ペア）")
    print("="*80)
    print()

    stops = find_gradient_stops(binary)

    # 重複を除去（同じ位置値のストップ）
    unique_stops = {}
    for offset, position, alpha in stops:
        key = f"{position:.2f}"
        if key not in unique_stops:
            unique_stops[key] = []
        unique_stops[key].append((offset, position, alpha))

    print(f"検出されたストップグループ: {len(unique_stops)} 個\n")

    for key in sorted(unique_stops.keys(), key=lambda x: float(x)):
        stop_list = unique_stops[key]
        print(f"Position {key} ({float(key)*100:.0f}%):")
        for offset, position, alpha in stop_list:
            print(f"  0x{offset:04x}: Position={position:.6f}, Alpha={alpha:.2f}")
        print()

    # 3. 各ストップと色の関係を解析
    print("="*80)
    print("3. ストップと色の空間的関係")
    print("="*80)
    print()

    # 各ユニークストップについて、近くの色を探す
    for key in sorted(unique_stops.keys(), key=lambda x: float(x)):
        stop_list = unique_stops[key]
        position_val = float(key)

        # 期待される色
        expected_color = ""
        if abs(position_val - 0.0) < 0.01:
            expected_color = "青 (Blue)"
        elif abs(position_val - 0.3) < 0.01:
            expected_color = "白 (White)"
        elif abs(position_val - 1.0) < 0.01:
            expected_color = "赤 (Red)"

        print(f"{position_val*100:.0f}%ストップ - 期待される色: {expected_color}")

        for offset, position, alpha in stop_list:
            print(f"\n  ストップ @ 0x{offset:04x}:")

            # 周辺64バイトで色を探す
            nearby_colors = []
            for color_offset, r, g, b, name, _, _ in colors:
                distance = color_offset - offset
                if -64 <= distance <= 64:
                    nearby_colors.append((distance, color_offset, r, g, b, name))

            if nearby_colors:
                print(f"  近くの色:")
                for distance, color_offset, r, g, b, name in sorted(nearby_colors, key=lambda x: abs(x[0])):
                    print(f"    {name:15s} @ 0x{color_offset:04x} (距離: {distance:+4d} bytes)")
            else:
                print(f"  近くに色なし")

        print()

    # 4. 各色の周辺を詳細表示
    print("="*80)
    print("4. 各色の周辺データ（16進ダンプ）")
    print("="*80)
    print()

    color_groups = {'青 (Blue)': [], '白 (White)': [], '赤 (Red)': []}
    for offset, r, g, b, name, _, _ in colors:
        if name in color_groups:
            color_groups[name].append(offset)

    for color_name, offsets in color_groups.items():
        print(f"\n{color_name}の位置: {len(offsets)} 箇所")
        for offset in offsets:
            print(f"\n  @ 0x{offset:04x}:")
            hex_dump_area(binary, offset, before=32, after=16)

    # 5. ファイル全体の構造マップ
    print("\n" + "="*80)
    print("5. ファイル構造マップ")
    print("="*80)
    print()

    # 全てのイベント（色とストップ）を位置順にソート
    events = []
    for offset, r, g, b, name, _, _ in colors:
        events.append((offset, 'COLOR', name, r, g, b))
    for offset, position, alpha in stops:
        events.append((offset, 'STOP', f"{position*100:.0f}%", position, alpha))

    events.sort()

    print("オフセット   種別      詳細")
    print("-" * 80)
    for event in events:
        offset = event[0]
        event_type = event[1]
        if event_type == 'COLOR':
            name = event[2]
            r, g, b = event[3], event[4], event[5]
            print(f"0x{offset:04x}    COLOR     {name:15s} RGB({r:3d}, {g:3d}, {b:3d})")
        else:
            percentage = event[2]
            position = event[3]
            alpha = event[4]
            print(f"0x{offset:04x}    STOP      {percentage:>4s} ストップ (pos={position:.2f}, alpha={alpha:.2f})")

if __name__ == "__main__":
    main()
