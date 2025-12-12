#!/usr/bin/env python3
"""
4色グラデーションの解析
黄赤青白グラ 10.25.75.90 の詳細解析
"""

import xml.etree.ElementTree as ET
import base64
import struct
import glob

def get_binary_from_prtextstyle(filepath):
    """prtextstyleファイルからバイナリを取得"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    for arb_param in root.findall('.//ArbVideoComponentParam'):
        name_elem = arb_param.find('.//Name')
        if name_elem is not None and ('Source Text' in name_elem.text or 'ソーステキスト' in name_elem.text):
            binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
            if binary_elem is not None and binary_elem.text:
                return base64.b64decode(binary_elem.text.strip())
    return None

def scan_for_specific_floats(binary, target_floats, tolerance=0.01):
    """特定のfloat値を検索"""
    found = []

    for offset in range(0, len(binary) - 3, 4):
        try:
            val = struct.unpack('<f', binary[offset:offset+4])[0]
            for target in target_floats:
                if abs(val - target) < tolerance:
                    found.append((offset, val, target))
        except:
            pass

    return found

def main():
    # 4色グラデーションファイルを探す
    files_10 = glob.glob("prtextstyle/*10.25.75.90*.prtextstyle")

    if not files_10:
        print("❌ 4色グラデーションファイルが見つかりません")
        return

    file_4color = files_10[0]

    print("="*80)
    print("4色グラデーションの解析")
    print("="*80)
    print(f"\nFile: {file_4color}\n")

    binary = get_binary_from_prtextstyle(file_4color)

    if not binary:
        print("❌ バイナリの取得に失敗")
        return

    print(f"バイナリサイズ: {len(binary)} bytes\n")

    # ファイル名から推測されるストップ位置
    target_positions = [0.10, 0.25, 0.75, 0.90]

    print("="*80)
    print(f"グラデーションストップ位置の検索（目標: {target_positions}）")
    print("="*80)
    print()

    found_positions = scan_for_specific_floats(binary, target_positions)

    print(f"検出された位置: {len(found_positions)} 箇所\n")

    # 位置ごとにグループ化
    by_target = {}
    for offset, val, target in found_positions:
        if target not in by_target:
            by_target[target] = []
        by_target[target].append((offset, val))

    for target in sorted(by_target.keys()):
        print(f"目標値 {target:.2f}:")
        for offset, val in by_target[target]:
            hex_context = binary[max(0, offset-8):offset+12].hex()
            print(f"  0x{offset:04x}: {val:.6f}")
            print(f"    Context: {hex_context}")
        print()

    # 連続する4つのfloat値を探す
    print("="*80)
    print("連続する4つのfloat値の検索（グラデーションストップのグループ）")
    print("="*80)
    print()

    for offset in range(0, len(binary) - 15, 4):
        try:
            vals = []
            for i in range(4):
                val = struct.unpack('<f', binary[offset+i*4:offset+i*4+4])[0]
                vals.append(val)

            # すべて0.0-1.0の範囲か？
            if all(0.0 <= v <= 1.0 for v in vals):
                # 昇順または降順か？
                is_sorted_asc = all(vals[i] <= vals[i+1] for i in range(3))
                is_sorted_desc = all(vals[i] >= vals[i+1] for i in range(3))

                if is_sorted_asc or is_sorted_desc:
                    # 目標値に近いか？
                    if any(abs(vals[i] - target_positions[i]) < 0.01 for i in range(min(4, len(vals)))):
                        print(f"0x{offset:04x}: {vals}")
                        print(f"  → 0.10={vals[0]:.2f}, 0.25={vals[1]:.2f}, 0.75={vals[2]:.2f}, 0.90={vals[3]:.2f}")

                        # 周辺のバイナリを表示
                        hex_dump = binary[offset:offset+16].hex()
                        print(f"  Hex: {hex_dump}")
                        print()
        except:
            pass

    # RGBA色の検索（グラデーションの各ストップの色）
    print("="*80)
    print("RGBA色の検索（グラデーション各ストップの色）")
    print("="*80)
    print()

    rgba_candidates = []
    for offset in range(0, len(binary) - 15, 4):
        try:
            r = struct.unpack('<f', binary[offset:offset+4])[0]
            g = struct.unpack('<f', binary[offset+4:offset+8])[0]
            b = struct.unpack('<f', binary[offset+8:offset+12])[0]
            a = struct.unpack('<f', binary[offset+12:offset+16])[0]

            if all(0.0 <= v <= 1.0 for v in [r, g, b, a]):
                # 少なくとも1つの値が0.5以上（純色に近い）
                if r > 0.5 or g > 0.5 or b > 0.5:
                    rgba_candidates.append((offset, r, g, b, a))
        except:
            pass

    print(f"検出されたRGBA候補: {len(rgba_candidates)} 箇所\n")

    for i, (offset, r, g, b, a) in enumerate(rgba_candidates[:10], 1):
        r255 = int(r * 255)
        g255 = int(g * 255)
        b255 = int(b * 255)
        a255 = int(a * 255)

        # 色の名前
        color_name = ""
        if r > 0.9 and g > 0.9 and b < 0.1:
            color_name = "黄"
        elif r > 0.9 and g < 0.1 and b < 0.1:
            color_name = "赤"
        elif r < 0.1 and g < 0.1 and b > 0.9:
            color_name = "青"
        elif r > 0.9 and g > 0.9 and b > 0.9:
            color_name = "白"

        print(f"{i}. 0x{offset:04x}: RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f})")
        print(f"   → RGB({r255:3d}, {g255:3d}, {b255:3d}, {a255:3d}) {color_name}")
        print()

if __name__ == "__main__":
    main()
