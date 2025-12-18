#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
発見した色データの位置を詳細解析
"""

from xml.etree import ElementTree as ET
import base64
import struct

def extract_binary(filepath: str) -> bytes:
    tree = ET.parse(filepath)
    root = tree.getroot()
    for param in root.findall(".//ArbVideoComponentParam"):
        name_elem = param.find("Name")
        if name_elem is not None and name_elem.text == "ソーステキスト":
            keyframe_val = param.find("StartKeyframeValue")
            if keyframe_val is not None and keyframe_val.text:
                if keyframe_val.attrib.get('Encoding', '') == 'base64':
                    return base64.b64decode(keyframe_val.text.strip())
    return b""

def hex_dump_region(binary: bytes, start: int, length: int) -> str:
    lines = []
    for i in range(start, min(start + length, len(binary)), 16):
        chunk = binary[i:i+16]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"{i:04x}:  {hex_part:<48}  {ascii_part}")
    return '\n'.join(lines)

def main():
    print("="*80)
    print("色データの位置詳細解析")
    print("="*80)

    files = {
        "White": "TEMPLATE_SolidFill_White.prtextstyle",
        "Red": "赤・ストローク無し.prtextstyle",
        "Blue": "青・ストローク無し.prtextstyle",
    }

    binaries = {}
    for name, filepath in files.items():
        binary = extract_binary(filepath)
        if binary:
            binaries[name] = binary
            print(f"✓ {name}: {len(binary)} bytes")

    # 発見した色データの位置
    color_locations = {
        "White": [0x00b5, 0x00b9, 0x00bd, 0x0159, 0x015d, 0x01a1],
        "Red": [0x01ab],
        "Blue": [0x01ad],
    }

    for name in ["White", "Red", "Blue"]:
        binary = binaries[name]
        locations = color_locations[name]

        print(f"\n{'='*80}")
        print(f"{name} の色データ解析")
        print(f"{'='*80}")

        for loc in locations:
            print(f"\n位置: 0x{loc:04x}")

            # RGB値を読み取る
            if loc + 3 <= len(binary):
                r = binary[loc]
                g = binary[loc+1]
                b = binary[loc+2]

                # さらに次のバイトも確認（アルファ？）
                a = binary[loc+3] if loc+3 < len(binary) else None

                print(f"  RGB: ({r}, {g}, {b})")
                if a is not None:
                    print(f"  Alpha: {a}")

            # 周辺データ（前後32バイト）
            context_start = max(0, loc - 32)
            context_end = min(len(binary), loc + 48)

            print(f"\n  周辺データ [{context_start:04x}-{context_end:04x}]:")
            for line in hex_dump_region(binary, context_start, context_end - context_start).split('\n'):
                # 該当位置をハイライト
                if f"{loc:04x}:" in line:
                    line += "  <<<< 色データ"
                print(f"    {line}")

    # 全ファイルの同じ位置を比較
    print(f"\n\n{'='*80}")
    print("全ファイルでの位置比較")
    print(f"{'='*80}")

    # 最も有力な位置を調べる
    # Redは0x01ab、Blueは0x01adだが、Whiteは0x01a1にある
    # これらは異なるオフセットなので、構造が違う可能性

    # とりあえず、0x01a0付近を全ファイルで比較
    print("\n0x01a0 付近の比較:")
    for name in ["White", "Red", "Blue"]:
        binary = binaries[name]
        print(f"\n{name}:")
        print(hex_dump_region(binary, 0x0190, 48))

    # 0x00b0 付近も比較（Whiteで複数のffffffff出現）
    print(f"\n\n0x00b0 付近の比較:")
    for name in ["White", "Red", "Blue"]:
        binary = binaries[name]
        print(f"\n{name}:")
        print(hex_dump_region(binary, 0x00a8, 48))

    # 0x0150 付近も比較
    print(f"\n\n0x0150 付近の比較:")
    for name in ["White", "Red", "Blue"]:
        binary = binaries[name]
        print(f"\n{name}:")
        print(hex_dump_region(binary, 0x0148, 48))

    print("\n" + "="*80)
    print("✅ 解析完了")
    print("="*80)

if __name__ == "__main__":
    main()
