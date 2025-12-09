#!/usr/bin/env python3
"""
全.prtextstyleファイルのhex比較表示
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


def get_style_name(file_path: str) -> str:
    """スタイル名を取得"""
    tree = ET.parse(file_path)
    root = tree.getroot()
    style_item = root.find(".//StyleProjectItem")
    if style_item is not None:
        name_elem = style_item.find(".//Name")
        if name_elem is not None and name_elem.text:
            return name_elem.text.strip()
    return Path(file_path).stem


def hex_dump_full(data: bytes, label: str):
    """完全なhexダンプ"""
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"サイズ: {len(data)} bytes")
    print(f"{'='*80}\n")

    for i in range(0, len(data), 16):
        offset = f"{i:04X}"
        chunk = data[i:min(i+16, len(data))]

        # Hex部分
        hex_parts = []
        for j in range(16):
            if j < len(chunk):
                hex_parts.append(f"{chunk[j]:02X}")
            else:
                hex_parts.append("  ")

        # 8バイトごとにスペース
        hex_str = " ".join(hex_parts[:8]) + "  " + " ".join(hex_parts[8:])

        # ASCII部分
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)

        print(f"{offset}  {hex_str}  |{ascii_str}|")


def hex_dump_side_by_side(data_dict: dict, start: int = 0, lines: int = 32):
    """複数ファイルをサイドバイサイドで比較"""
    print(f"\n{'='*100}")
    print(f"サイドバイサイド比較 (オフセット 0x{start:04X} - 0x{start + lines*16:04X})")
    print(f"{'='*100}\n")

    # ヘッダー
    files = list(data_dict.keys())
    for i, name in enumerate(files):
        print(f"[{i}] {name}")
    print()

    # データ比較
    for line_num in range(lines):
        offset = start + line_num * 16
        print(f"0x{offset:04X}:")

        for name, data in data_dict.items():
            if offset < len(data):
                chunk = data[offset:min(offset+16, len(data))]
                hex_str = " ".join(f"{b:02X}" for b in chunk)
                print(f"  [{files.index(name)}] {hex_str}")
            else:
                print(f"  [{files.index(name)}] (EOF)")
        print()


def compare_all_at_offset(data_dict: dict, offset: int, length: int = 16):
    """特定オフセットでの全ファイル比較"""
    print(f"\n{'='*80}")
    print(f"オフセット 0x{offset:04X} での比較 ({length} bytes)")
    print(f"{'='*80}\n")

    for name, data in data_dict.items():
        if offset + length <= len(data):
            chunk = data[offset:offset+length]
            hex_str = " ".join(f"{b:02X}" for b in chunk)

            # RGB値を検出
            rgb_annotations = []
            for i in range(len(chunk) - 2):
                r, g, b = chunk[i], chunk[i+1], chunk[i+2]
                if (r == 255 or g == 255 or b == 255) or (r == 0 and g == 0 and b == 255):
                    rgb_annotations.append(f"+{i:02X}:RGB({r},{g},{b})")

            annotation = " " + ", ".join(rgb_annotations) if rgb_annotations else ""
            print(f"{name:30s}: {hex_str}{annotation}")
        else:
            print(f"{name:30s}: (範囲外)")


if __name__ == "__main__":
    print("="*80)
    print("全 .prtextstyle ファイルの Hex 比較")
    print("="*80)

    # ファイル収集
    files = list(Path(".").glob("*.prtextstyle"))
    print(f"\n見つかったファイル: {len(files)}個\n")

    data_dict = {}
    for file_path in sorted(files):
        binary = extract_binary(str(file_path))
        if binary:
            style_name = get_style_name(str(file_path))
            data_dict[style_name] = binary
            print(f"✓ {style_name:30s} ({len(binary):4d} bytes)")

    print("\n" + "="*80)
    print("モード選択")
    print("="*80)
    print("\n1. 全ファイルの完全hexダンプ")
    print("2. サイドバイサイド比較（指定範囲）")
    print("3. 重要オフセットでの比較")
    print("4. すべて実行")

    mode = "4"  # デフォルトはすべて実行

    if mode in ["1", "4"]:
        print("\n" + "="*80)
        print("【モード1】全ファイルの完全hexダンプ")
        print("="*80)

        for name, data in data_dict.items():
            hex_dump_full(data, name)

    if mode in ["2", "4"]:
        print("\n" + "="*80)
        print("【モード2】サイドバイサイド比較")
        print("="*80)

        # 重要な範囲
        ranges = [
            (0x0000, 16, "ヘッダ部分"),
            (0x00B0, 16, "Stroke色候補領域"),
            (0x0180, 16, "中間部"),
            (0x01A0, 16, "Fill色候補領域（単色）"),
            (0x0240, 16, "グラデーション領域（2色）"),
        ]

        for start, lines, desc in ranges:
            print(f"\n--- {desc} ---")
            hex_dump_side_by_side(data_dict, start, lines)

    if mode in ["3", "4"]:
        print("\n" + "="*80)
        print("【モード3】重要オフセットでの比較")
        print("="*80)

        # RGB値が見つかった重要なオフセット
        important_offsets = [
            (0x00B8, 16, "Stroke色領域1"),
            (0x01AB, 16, "Fill色領域（赤ファイル）"),
            (0x01AD, 16, "Fill色領域（青ファイル）"),
            (0x0249, 16, "グラデーション領域（2色）"),
            (0x0279, 16, "グラデーション領域（3色）"),
        ]

        for offset, length, desc in important_offsets:
            compare_all_at_offset(data_dict, offset, length)

    # サマリー
    print("\n" + "="*80)
    print("サマリー")
    print("="*80)

    print("\nファイルサイズ:")
    for name, data in sorted(data_dict.items(), key=lambda x: len(x[1])):
        print(f"  {len(data):4d} bytes - {name}")

    # RGB値の出現箇所をカウント
    print("\nRGB(255,255,255)の出現回数:")
    white_pattern = b'\xFF\xFF\xFF'
    for name, data in data_dict.items():
        count = data.count(white_pattern)
        print(f"  {count:2d}回 - {name}")

    print("\nRGB(255,0,0)の出現回数:")
    red_pattern = b'\xFF\x00\x00'
    for name, data in data_dict.items():
        count = data.count(red_pattern)
        print(f"  {count:2d}回 - {name}")

    print("\nRGB(0,0,255)の出現回数:")
    blue_pattern = b'\x00\x00\xFF'
    for name, data in data_dict.items():
        count = data.count(blue_pattern)
        print(f"  {count:2d}回 - {name}")
