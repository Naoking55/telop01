#!/usr/bin/env python3
"""
青白赤グラ 30 vs 70 の完全比較
Position値と色の関係を解明
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
    """RGBA float形式の色を検索"""
    colors = []
    for offset in range(0, len(binary) - 15, 4):
        try:
            r = struct.unpack('<f', binary[offset:offset+4])[0]
            g = struct.unpack('<f', binary[offset+4:offset+8])[0]
            b = struct.unpack('<f', binary[offset+8:offset+12])[0]
            a = struct.unpack('<f', binary[offset+12:offset+16])[0]

            if all(-0.1 <= v <= 1.1 for v in [r, g, b, a]):
                color_name = ''
                if abs(b - 1.0) < 0.1 and abs(r) < 0.1 and abs(g) < 0.1:
                    color_name = '青'
                elif abs(r - 1.0) < 0.1 and abs(g - 1.0) < 0.1 and abs(b - 1.0) < 0.1:
                    color_name = '白'
                elif abs(r - 1.0) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1:
                    color_name = '赤'

                if color_name:
                    colors.append((offset, r, g, b, a, color_name))
        except:
            pass
    return colors

def find_rgb_byte_colors(binary):
    """RGB bytes形式の色を検索"""
    colors = []
    for offset in range(0, len(binary) - 2):
        r, g, b = binary[offset:offset+3]

        color_name = ''
        if r == 255 and g == 255 and b == 255:
            color_name = '白'
        elif r == 255 and g == 0 and b == 0:
            color_name = '赤'
        elif r == 0 and g == 0 and b == 255:
            color_name = '青'

        if color_name:
            colors.append((offset, r, g, b, color_name))

    return colors

def find_gradient_stops(binary):
    """グラデーションストップを検索"""
    stops = []
    for offset in range(0, len(binary) - 7, 4):
        try:
            position = struct.unpack('<f', binary[offset:offset+4])[0]
            alpha = struct.unpack('<f', binary[offset+4:offset+8])[0]

            if 0.0 <= position <= 1.0 and 0.3 <= alpha <= 1.0:
                stops.append((offset, position, alpha))
        except:
            pass
    return stops

def main():
    files_30 = glob.glob('prtextstyle/*青白赤*30.prtextstyle')
    files_70 = glob.glob('prtextstyle/*青白赤*70.prtextstyle')

    if not files_30 or not files_70:
        print("❌ グラデーションファイルが見つかりません")
        return

    file_30 = files_30[0]
    file_70 = files_70[0]

    print("="*80)
    print("青白赤グラデーション 30% vs 70% 完全比較")
    print("="*80)
    print()

    print(f"30%ファイル: {file_30}")
    print(f"70%ファイル: {file_70}")
    print()

    bin_30 = get_binary_from_prtextstyle(file_30)
    bin_70 = get_binary_from_prtextstyle(file_70)

    if not bin_30 or not bin_70:
        print("❌ バイナリ取得失敗")
        return

    print(f"30%サイズ: {len(bin_30)} bytes")
    print(f"70%サイズ: {len(bin_70)} bytes")
    print()

    # グラデーションストップを検出
    print("="*80)
    print("グラデーションストップの比較")
    print("="*80)
    print()

    stops_30 = find_gradient_stops(bin_30)
    stops_70 = find_gradient_stops(bin_70)

    # Position値でグループ化
    def group_by_position(stops):
        groups = {}
        for offset, position, alpha in stops:
            # 0.29-0.31を30%, 0.69-0.71を70%としてグループ化
            if 0.29 <= position <= 0.31:
                key = "30%"
            elif 0.69 <= position <= 0.71:
                key = "70%"
            elif position < 0.01:
                key = "0%"
            elif position > 0.99:
                key = "100%"
            else:
                key = f"{position*100:.0f}%"

            if key not in groups:
                groups[key] = []
            groups[key].append((offset, position, alpha))
        return groups

    groups_30 = group_by_position(stops_30)
    groups_70 = group_by_position(stops_70)

    print("30%ファイルのストップ:")
    for key in sorted(groups_30.keys(), key=lambda x: float(x.replace('%', ''))):
        print(f"\n  {key}:")
        for offset, position, alpha in groups_30[key]:
            print(f"    0x{offset:04x}: Position={position:.6f}, Alpha={alpha:.2f}")

    print("\n" + "-"*80)
    print("\n70%ファイルのストップ:")
    for key in sorted(groups_70.keys(), key=lambda x: float(x.replace('%', ''))):
        print(f"\n  {key}:")
        for offset, position, alpha in groups_70[key]:
            print(f"    0x{offset:04x}: Position={position:.6f}, Alpha={alpha:.2f}")

    # RGBA float色を検出
    print("\n" + "="*80)
    print("RGBA Float色の比較")
    print("="*80)
    print()

    rgba_30 = find_rgba_float_colors(bin_30)
    rgba_70 = find_rgba_float_colors(bin_70)

    print(f"30%ファイル: {len(rgba_30)} 箇所")
    for offset, r, g, b, a, color_name in rgba_30:
        print(f"  0x{offset:04x}: {color_name} RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f})")

    print(f"\n70%ファイル: {len(rgba_70)} 箇所")
    for offset, r, g, b, a, color_name in rgba_70:
        print(f"  0x{offset:04x}: {color_name} RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f})")

    # RGB bytes色を検出
    print("\n" + "="*80)
    print("RGB Bytes色の比較")
    print("="*80)
    print()

    rgb_30 = find_rgb_byte_colors(bin_30)
    rgb_70 = find_rgb_byte_colors(bin_70)

    print(f"30%ファイル: {len(rgb_30)} 箇所")
    for color in ['青', '白', '赤']:
        matching = [c for c in rgb_30 if c[4] == color]
        print(f"\n  {color}: {len(matching)} 箇所")
        for offset, r, g, b, _ in matching[:5]:  # 最初の5箇所のみ
            print(f"    0x{offset:04x}: RGB({r:3d}, {g:3d}, {b:3d})")

    print(f"\n70%ファイル: {len(rgb_70)} 箇所")
    for color in ['青', '白', '赤']:
        matching = [c for c in rgb_70 if c[4] == color]
        print(f"\n  {color}: {len(matching)} 箇所")
        for offset, r, g, b, _ in matching[:5]:  # 最初の5箇所のみ
            print(f"    0x{offset:04x}: RGB({r:3d}, {g:3d}, {b:3d})")

    # 30%と70%の中間ストップの色を比較
    print("\n" + "="*80)
    print("中間ストップ（30% vs 70%）の色データ")
    print("="*80)
    print()

    # 30%ファイルの30%ストップ
    if "30%" in groups_30:
        print("30%ファイルの30%ストップ:")
        for offset, position, alpha in groups_30["30%"]:
            print(f"\n  ストップ @ 0x{offset:04x} (Position={position:.6f})")

            # 近くの色を探す
            print(f"    近くのRGBA Float色:")
            for rgba_offset, r, g, b, a, color_name in rgba_30:
                distance = rgba_offset - offset
                if -20 <= distance <= 20:
                    print(f"      {color_name} @ 0x{rgba_offset:04x} (距離: {distance:+4d})")

            print(f"    近くのRGB Bytes色:")
            for rgb_offset, r, g, b, color_name in rgb_30:
                distance = rgb_offset - offset
                if -20 <= distance <= 20:
                    print(f"      {color_name} @ 0x{rgb_offset:04x} (距離: {distance:+4d})")

    # 70%ファイルの70%ストップ
    if "70%" in groups_70:
        print("\n70%ファイルの70%ストップ:")
        for offset, position, alpha in groups_70["70%"]:
            print(f"\n  ストップ @ 0x{offset:04x} (Position={position:.6f})")

            # 近くの色を探す
            print(f"    近くのRGBA Float色:")
            for rgba_offset, r, g, b, a, color_name in rgba_70:
                distance = rgba_offset - offset
                if -20 <= distance <= 20:
                    print(f"      {color_name} @ 0x{rgba_offset:04x} (距離: {distance:+4d})")

            print(f"    近くのRGB Bytes色:")
            for rgb_offset, r, g, b, color_name in rgb_70:
                distance = rgb_offset - offset
                if -20 <= distance <= 20:
                    print(f"      {color_name} @ 0x{rgb_offset:04x} (距離: {distance:+4d})")

    # 結論
    print("\n" + "="*80)
    print("結論")
    print("="*80)
    print()

    print("【Position値と色の対応】")
    print()

    if "30%" in groups_30:
        stop_30 = groups_30["30%"][0]
        print(f"30%ファイル:")
        print(f"  30%ストップ @ 0x{stop_30[0]:04x}: Position={stop_30[1]:.6f}")
        print(f"  → 期待される色: 白")

    if "70%" in groups_70:
        stop_70 = groups_70["70%"][0]
        print(f"\n70%ファイル:")
        print(f"  70%ストップ @ 0x{stop_70[0]:04x}: Position={stop_70[1]:.6f}")
        print(f"  → 期待される色: 白")

    print("\n【仮説検証】")
    print()
    print("もし Position 値が正しく グラデーション位置 を表すなら:")
    print("  30%ストップの近くに 白色 が存在するはず")
    print("  70%ストップの近くに 白色 が存在するはず")

if __name__ == "__main__":
    main()
