#!/usr/bin/env python3
"""
単色ファイルの比較で色データ位置を特定
白・ストローク無し vs 赤・ストローク無し vs 青・ストローク無し
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

def find_rgb_bytes(binary):
    """RGB bytes形式（0-255）の色を探す"""
    colors = []

    # VTable領域をスキップ
    search_start = 0x0150

    for i in range(search_start, len(binary) - 2):
        r, g, b = binary[i], binary[i+1], binary[i+2]

        # 特定の色パターン
        if (r == 255 and g == 255 and b == 255):  # 白
            colors.append(('白', i, r, g, b))
        elif (r == 255 and g == 0 and b == 0):  # 赤
            colors.append(('赤', i, r, g, b))
        elif (r == 0 and g == 0 and b == 255):  # 青
            colors.append(('青', i, r, g, b))

    return colors

def main():
    # 単色ファイルを探す
    files = {
        '白': glob.glob("prtextstyle/*白*ストローク無し.prtextstyle"),
        '赤': glob.glob("prtextstyle/*赤*ストローク無し.prtextstyle"),
        '青': glob.glob("prtextstyle/*青*ストローク無し.prtextstyle")
    }

    print("="*80)
    print("単色ファイルの色データ位置解析")
    print("="*80)
    print()

    binaries = {}

    for color, file_list in files.items():
        if file_list:
            file_path = file_list[0]
            binary = get_binary_from_prtextstyle(file_path)

            if binary:
                binaries[color] = binary
                print(f"{color}色ファイル: {len(binary)} bytes")

                # RGB bytes形式で色を探す
                found_colors = find_rgb_bytes(binary)

                if found_colors:
                    print(f"  検出された色:")
                    for name, offset, r, g, b in found_colors:
                        print(f"    {name} @ 0x{offset:04x}: RGB({r}, {g}, {b})")
                else:
                    print(f"  色が見つかりませんでした")
                print()
            else:
                print(f"{color}色ファイル: バイナリ取得失敗")
                print()

    # 3つのファイルを比較
    if len(binaries) == 3:
        print("="*80)
        print("3色の差分解析:")
        print("="*80)
        print()

        # サイズを確認
        sizes = {color: len(binary) for color, binary in binaries.items()}
        print(f"サイズ: {sizes}")

        if len(set(sizes.values())) == 1:
            print("→ すべて同じサイズ")
            print()

            # バイト単位で比較
            min_len = min(sizes.values())
            differences = []

            for i in range(min_len):
                values = {color: binary[i] for color, binary in binaries.items()}
                if len(set(values.values())) > 1:  # 値が異なる
                    differences.append((i, values))

            print(f"差分バイト数: {len(differences)}")
            print()

            print("最初の20個の差分:")
            for i, (offset, values) in enumerate(differences[:20], 1):
                print(f"{i:2d}. 0x{offset:04x}:")
                for color in ['白', '赤', '青']:
                    if color in values:
                        print(f"    {color}: 0x{values[color]:02x} ({values[color]:3d})")
                print()

            # RGBバイトパターンを探す
            print("="*80)
            print("RGB bytesパターンの検索（連続3バイト）:")
            print("="*80)
            print()

            for color, binary in binaries.items():
                print(f"{color}色ファイル:")

                # 0x0150以降でRGBパターンを探す
                for offset in range(0x0150, len(binary) - 2):
                    r, g, b = binary[offset:offset+3]

                    # 白: (255, 255, 255)
                    if color == '白' and r == 255 and g == 255 and b == 255:
                        context = binary[max(0, offset-8):offset+11].hex()
                        print(f"  0x{offset:04x}: RGB({r:3d}, {g:3d}, {b:3d})")
                        print(f"    Context: {context}")

                    # 赤: (255, 0, 0)
                    elif color == '赤' and r == 255 and g == 0 and b == 0:
                        context = binary[max(0, offset-8):offset+11].hex()
                        print(f"  0x{offset:04x}: RGB({r:3d}, {g:3d}, {b:3d})")
                        print(f"    Context: {context}")

                    # 青: (0, 0, 255)
                    elif color == '青' and r == 0 and g == 0 and b == 255:
                        context = binary[max(0, offset-8):offset+11].hex()
                        print(f"  0x{offset:04x}: RGB({r:3d}, {g:3d}, {b:3d})")
                        print(f"    Context: {context}")
                print()

if __name__ == "__main__":
    main()
