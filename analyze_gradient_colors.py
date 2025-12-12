#!/usr/bin/env python3
"""
グラデーションストップのRGB色マッピング
青白赤グラ 30 の解析
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

def scan_for_rgba_floats(binary):
    """RGBAカラー候補をスキャン"""
    candidates = []

    for offset in range(0, len(binary) - 15, 4):
        try:
            r = struct.unpack('<f', binary[offset:offset+4])[0]
            g = struct.unpack('<f', binary[offset+4:offset+8])[0]
            b = struct.unpack('<f', binary[offset+8:offset+12])[0]
            a = struct.unpack('<f', binary[offset+12:offset+16])[0]

            # 0.0-1.0の範囲内か
            if all(0.0 <= v <= 1.0 for v in [r, g, b, a]):
                # 少なくとも1つの値が0.5以上（純色に近い）
                if r > 0.3 or g > 0.3 or b > 0.3:
                    candidates.append((offset, r, g, b, a))
        except:
            pass

    return candidates

def identify_color(r, g, b):
    """色を識別"""
    if r > 0.8 and g > 0.8 and b > 0.8:
        return "白"
    elif r > 0.8 and g < 0.2 and b < 0.2:
        return "赤"
    elif r < 0.2 and g < 0.2 and b > 0.8:
        return "青"
    elif r > 0.8 and g > 0.8 and b < 0.2:
        return "黄"
    elif r < 0.2 and g < 0.2 and b < 0.2:
        return "黒"
    else:
        return "?"

def main():
    # 青白赤グラファイルを解析
    files = glob.glob("prtextstyle/*青白赤*.prtextstyle")

    if not files:
        print("❌ 青白赤グラファイルが見つかりません")
        return

    file_path = files[0]

    print("="*80)
    print("青白赤グラデーションの色マッピング解析")
    print("="*80)
    print(f"\nFile: {file_path}\n")

    binary = get_binary_from_prtextstyle(file_path)

    if not binary:
        print("❌ バイナリの取得に失敗")
        return

    print(f"バイナリサイズ: {len(binary)} bytes\n")

    # グラデーションストップ位置を既知として使用
    # 青白赤グラは3色なので、0%, 中間%, 100%の3つのストップがあるはず
    print("="*80)
    print("想定されるグラデーション構造:")
    print("="*80)
    print()
    print("  0%: 青")
    print(" 30%: 白（中間ストップ）")
    print("100%: 赤")
    print()

    # RGBAカラー候補をスキャン
    print("="*80)
    print("RGBA候補の検出:")
    print("="*80)
    print()

    candidates = scan_for_rgba_floats(binary)

    print(f"検出された候補: {len(candidates)} 箇所\n")

    # 青、白、赤を探す
    colors_found = {}

    for offset, r, g, b, a in candidates:
        color_name = identify_color(r, g, b)

        if color_name in ["青", "白", "赤"]:
            if color_name not in colors_found:
                colors_found[color_name] = []
            colors_found[color_name].append((offset, r, g, b, a))

    # 発見した色を表示
    print("発見した色:")
    print()

    for color in ["青", "白", "赤"]:
        if color in colors_found:
            print(f"{color}色:")
            for offset, r, g, b, a in colors_found[color]:
                r255 = int(r * 255)
                g255 = int(g * 255)
                b255 = int(b * 255)
                a255 = int(a * 255)
                print(f"  0x{offset:04x}: RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f})")
                print(f"          → RGB({r255:3d}, {g255:3d}, {b255:3d}, {a255:3d})")
            print()
        else:
            print(f"{color}色: 見つかりませんでした")
            print()

    # 全候補を表示（デバッグ用）
    print("="*80)
    print("全RGBA候補（最初の20個）:")
    print("="*80)
    print()

    for i, (offset, r, g, b, a) in enumerate(candidates[:20], 1):
        r255 = int(r * 255)
        g255 = int(g * 255)
        b255 = int(b * 255)
        a255 = int(a * 255)

        color_name = identify_color(r, g, b)

        print(f"{i:2d}. 0x{offset:04x}: RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f})")
        print(f"    → RGB({r255:3d}, {g255:3d}, {b255:3d}, {a255:3d}) {color_name}")

    # 0x0190-0x0220の範囲を詳しく見る（グラデーション色データ領域）
    print()
    print("="*80)
    print("0x0190-0x0220領域の16進ダンプ（グラデーション色データ領域）:")
    print("="*80)
    print()

    for i in range(0x190, 0x220, 16):
        hex_str = ' '.join(f'{b:02x}' for b in binary[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in binary[i:i+16])
        print(f'{i:04x}  {hex_str:<48}  |{ascii_str}|')

if __name__ == "__main__":
    main()
