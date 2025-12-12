#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prtextstyle ファイル解析ツール
生成されたバイナリデータの内容を詳しく表示
"""

import sys
import base64
import struct
from xml.etree import ElementTree as ET

def analyze_prtextstyle(filepath: str):
    """prtextstyle ファイルを解析"""
    print("=" * 70)
    print(f"prtextstyle 解析: {filepath}")
    print("=" * 70)

    # XMLを読み込み
    tree = ET.parse(filepath)
    root = tree.getroot()

    print(f"\nXML ルート: <{root.tag}>")
    print(f"バージョン: {root.attrib.get('Version', 'N/A')}")

    # Styleを取得
    styles = root.findall(".//Style")
    print(f"\nスタイル数: {len(styles)}")

    for i, style in enumerate(styles, 1):
        print(f"\n{'='*70}")
        print(f"スタイル {i}")
        print(f"{'='*70}")

        # 名前
        name_elem = style.find("Name")
        if name_elem is not None and name_elem.text:
            print(f"名前: {name_elem.text}")

        # BinaryData
        binary_elem = style.find("BinaryData")
        if binary_elem is not None and binary_elem.text:
            encoding = binary_elem.attrib.get("Encoding", "unknown")
            print(f"エンコーディング: {encoding}")

            if encoding == "base64":
                # Base64デコード
                try:
                    binary_data = base64.b64decode(binary_elem.text.strip())
                    print(f"バイナリサイズ: {len(binary_data)} bytes")
                    print(f"\nバイナリデータ (hex):")
                    print_hex(binary_data)

                    # TLV解析
                    print(f"\nTLV 構造解析:")
                    parse_tlv(binary_data)

                except Exception as e:
                    print(f"✗ Base64デコードエラー: {e}")

def print_hex(data: bytes, bytes_per_line: int = 16):
    """バイナリデータを16進数で表示"""
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i+bytes_per_line]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"{i:04x}:  {hex_part:<48}  {ascii_part}")

def parse_tlv(data: bytes):
    """TLV構造を解析"""
    offset = 0
    tlv_index = 1

    while offset < len(data):
        if offset + 6 > len(data):
            print(f"  ⚠ データ不足 (offset={offset}, 残り={len(data)-offset} bytes)")
            break

        # Tag (2 bytes, little-endian)
        tag = struct.unpack("<H", data[offset:offset+2])[0]
        offset += 2

        # Length (4 bytes, little-endian)
        length = struct.unpack("<I", data[offset:offset+4])[0]
        offset += 4

        # Value
        if offset + length > len(data):
            print(f"  ✗ TLV #{tlv_index}: Tag=0x{tag:04x}, Length={length} (データ範囲外)")
            break

        value = data[offset:offset+length]
        offset += length

        # TLV情報を表示
        print(f"\n  TLV #{tlv_index}: Tag=0x{tag:04x}, Length={length}")
        print(f"    タグ名: {get_tag_name(tag)}")
        print(f"    値 (hex): {value.hex()}")

        # タグに応じて値を解釈
        interpret_value(tag, value)

        tlv_index += 1

def get_tag_name(tag: int) -> str:
    """タグIDから名前を取得"""
    tag_names = {
        0x0001: "Font Name (フォント名)",
        0x0002: "Font Style (太字/斜体フラグ)",
        0x0003: "Font Size (フォントサイズ)",
        0x0004: "Fill Color (単色)",
        0x0005: "Gradient Fill (グラデーション)",
        0x0006: "Stroke (ストローク)",
        0x0007: "Shadow (シャドウ)",
        0x000A: "Gradient Angle (グラデーション角度)",
        0x00F0: "Gradient Stop (グラデーションストップ)",
    }
    return tag_names.get(tag, "Unknown")

def interpret_value(tag: int, value: bytes):
    """値を解釈して表示"""
    try:
        if tag == 0x0001:  # Font Name
            font_name = value.decode('utf-8')
            print(f"    → フォント名: '{font_name}'")

        elif tag == 0x0002:  # Font Style
            if len(value) >= 4:
                flags = struct.unpack("<I", value[:4])[0]
                bold = bool(flags & 1)
                italic = bool(flags & 2)
                print(f"    → 太字: {bold}, 斜体: {italic}")

        elif tag == 0x0003:  # Font Size
            if len(value) >= 4:
                size = struct.unpack("<f", value[:4])[0]
                print(f"    → サイズ: {size}pt")

        elif tag == 0x0004:  # Fill Color
            if len(value) >= 4:
                r, g, b, a = value[0], value[1], value[2], value[3]
                print(f"    → RGBA: ({r}, {g}, {b}, {a})")

        elif tag == 0x0007:  # Shadow
            if len(value) >= 16:
                ox, oy, blur = struct.unpack("<fff", value[:12])
                r, g, b, a = value[12], value[13], value[14], value[15]
                print(f"    → オフセット: ({ox:.2f}, {oy:.2f})")
                print(f"    → ぼかし: {blur:.2f}")
                print(f"    → 色: RGBA({r}, {g}, {b}, {a})")

        elif tag == 0x000A:  # Gradient Angle
            if len(value) >= 4:
                angle = struct.unpack("<f", value[:4])[0]
                print(f"    → 角度: {angle}°")

        elif tag == 0x00F0:  # Gradient Stop
            if len(value) >= 24:
                pos, mid = struct.unpack("<ff", value[:8])
                r, g, b, a = struct.unpack("<IIII", value[8:24])
                print(f"    → 位置: {pos:.3f}, 中間点: {mid:.3f}")
                print(f"    → RGBA: ({r}, {g}, {b}, {a})")

    except Exception as e:
        print(f"    ⚠ 解釈エラー: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python analyze_prtextstyle.py <prtextstyle_file>")
        sys.exit(1)

    analyze_prtextstyle(sys.argv[1])
