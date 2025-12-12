#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prtextstyle のバイナリデータを完全デコード
"""

from xml.etree import ElementTree as ET
import base64
import struct
import sys

def decode_binary_data(prtextstyle_file):
    """バイナリデータを解析"""

    tree = ET.parse(prtextstyle_file)
    root = tree.getroot()

    # ArbVideoComponentParam を探す
    arb_params = root.findall(".//ArbVideoComponentParam")

    print("=" * 80)
    print(f"バイナリデータ解析: {prtextstyle_file}")
    print("=" * 80)

    for idx, param in enumerate(arb_params, 1):
        name_elem = param.find("Name")
        name = name_elem.text if name_elem is not None else "?"

        print(f"\n{'='*80}")
        print(f"Param {idx}: {name}")
        print(f"{'='*80}")

        keyframe_val = param.find("StartKeyframeValue")
        if keyframe_val is None or not keyframe_val.text:
            print("  バイナリデータなし")
            continue

        encoding = keyframe_val.attrib.get('Encoding', '?')
        binary_hash = keyframe_val.attrib.get('BinaryHash', '?')

        print(f"Encoding: {encoding}")
        print(f"BinaryHash: {binary_hash}")

        if encoding != 'base64':
            print("  base64以外のエンコーディング")
            continue

        # Base64デコード
        try:
            binary = base64.b64decode(keyframe_val.text.strip())
            print(f"\nバイナリサイズ: {len(binary)} bytes")

            # Hex dump
            print("\nHex dump (全体):")
            for i in range(0, len(binary), 16):
                chunk = binary[i:i+16]
                hex_part = ' '.join(f'{b:02x}' for b in chunk)
                ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                print(f"{i:04x}:  {hex_part:<48}  {ascii_part}")

            # 構造解析を試みる
            print("\n" + "="*80)
            print("構造解析")
            print("="*80)

            offset = 0
            field_num = 1

            while offset < len(binary):
                remaining = len(binary) - offset

                if remaining < 4:
                    print(f"\n[残り {remaining} bytes - 解析終了]")
                    break

                print(f"\n--- オフセット 0x{offset:04x} ({offset}) ---")

                # 最初の4バイトを色々な形式で表示
                bytes4 = binary[offset:offset+4]

                # uint32 (little-endian)
                uint32_le = struct.unpack("<I", bytes4)[0]
                print(f"uint32 (LE): {uint32_le} (0x{uint32_le:08x})")

                # int32 (little-endian)
                int32_le = struct.unpack("<i", bytes4)[0]
                print(f"int32 (LE):  {int32_le}")

                # float (little-endian)
                float_le = struct.unpack("<f", bytes4)[0]
                print(f"float (LE):  {float_le}")

                # Bytes as is
                print(f"Bytes: {bytes4.hex()}")

                # ASCII (if printable)
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in bytes4)
                if any(32 <= b < 127 for b in bytes4):
                    print(f"ASCII: '{ascii_str}'")

                # 次の8バイトも見る
                if offset + 8 <= len(binary):
                    bytes8 = binary[offset:offset+8]
                    print(f"次8バイト: {bytes8.hex()}")

                # パターン認識
                # 文字列の長さっぽい？
                if 0 < uint32_le < 1000:
                    print(f"→ 長さフィールドの可能性: {uint32_le}")
                    if offset + 4 + uint32_le <= len(binary):
                        potential_str = binary[offset+4:offset+4+uint32_le]
                        try:
                            decoded = potential_str.decode('utf-8')
                            print(f"→ 次のデータ（UTF-8）: '{decoded}'")
                        except:
                            print(f"→ 次のデータ（hex）: {potential_str[:32].hex()}...")

                field_num += 1

                # インタラクティブに進める
                if field_num > 20:  # 最初の20フィールドだけ
                    print("\n[最初の20フィールドまで表示]")
                    break

                offset += 4  # 次の4バイトへ

        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        files = ["TEMPLATE_SolidFill_White.prtextstyle"]
    else:
        files = sys.argv[1:]

    for f in files:
        decode_binary_data(f)
        print("\n\n")
