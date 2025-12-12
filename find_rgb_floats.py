#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RGB色のfloat値を探す
"""

from xml.etree import ElementTree as ET
import base64
import struct
import sys

def extract_binary(filepath: str) -> bytes:
    """prtextstyle からバイナリデータを抽出"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    for param in root.findall(".//ArbVideoComponentParam"):
        name_elem = param.find("Name")
        if name_elem is not None and name_elem.text == "ソーステキスト":
            keyframe_val = param.find("StartKeyframeValue")
            if keyframe_val is not None and keyframe_val.text:
                encoding = keyframe_val.attrib.get('Encoding', '')
                if encoding == 'base64':
                    return base64.b64decode(keyframe_val.text.strip())
    return b""

def find_rgb_patterns(binary: bytes, name: str):
    """RGB色のパターンを探す"""
    print(f"\n{'='*80}")
    print(f"{name} の RGB パターン検索")
    print(f"{'='*80}")

    # 3つのfloat (RGB) を探す
    print("\n[3連続float (RGB)]")
    for i in range(0, len(binary) - 11, 1):
        try:
            r, g, b = struct.unpack("<fff", binary[i:i+12])

            # 全て0.0-1.0の範囲
            if all(-0.01 <= v <= 1.01 for v in [r, g, b]):
                # 全て0.0や全て1.0は除外
                if not (all(abs(v) < 0.01 for v in [r, g, b]) or all(abs(v - 1.0) < 0.01 for v in [r, g, b])):
                    print(f"  0x{i:04x}: R={r:.6f}, G={g:.6f}, B={b:.6f}")
        except:
            pass

    # 4つのfloat (RGBA) を探す
    print("\n[4連続float (RGBA)]")
    for i in range(0, len(binary) - 15, 1):
        try:
            r, g, b, a = struct.unpack("<ffff", binary[i:i+16])

            # 全て0.0-1.0の範囲
            if all(-0.01 <= v <= 1.01 for v in [r, g, b, a]):
                # 全て0.0は除外
                if not all(abs(v) < 0.01 for v in [r, g, b, a]):
                    # アルファが1.0付近か、少なくとも1つの色成分が0でない
                    if abs(a - 1.0) < 0.01 or any(abs(v) > 0.01 for v in [r, g, b]):
                        print(f"  0x{i:04x}: R={r:.6f}, G={g:.6f}, B={b:.6f}, A={a:.6f}")
        except:
            pass

def compare_specific_offsets(binaries: dict):
    """特定のオフセットを比較"""
    print("\n" + "="*80)
    print("特定オフセットの比較")
    print("="*80)

    # 各種オフセットを試す
    test_offsets = [
        0x0090, 0x0098, 0x00a0, 0x00a8,
        0x0100, 0x0110, 0x0120, 0x0130,
        0x0150, 0x0160, 0x0170, 0x0180,
        0x01a0, 0x01b0, 0x01c0,
    ]

    for offset in test_offsets:
        print(f"\n[0x{offset:04x}]")
        for name, binary in binaries.items():
            if offset + 16 <= len(binary):
                chunk = binary[offset:offset+16]

                # Hex
                hex_str = ' '.join(f'{b:02x}' for b in chunk)

                # RGBA float
                try:
                    r, g, b, a = struct.unpack("<ffff", chunk)
                    if all(-0.01 <= v <= 1.01 for v in [r, g, b, a]):
                        print(f"  {name:12s}: R={r:.3f}, G={g:.3f}, B={b:.3f}, A={a:.3f}")
                    else:
                        print(f"  {name:12s}: {hex_str}")
                except:
                    print(f"  {name:12s}: {hex_str}")

def main():
    print("="*80)
    print("RGB Float 値の探索")
    print("="*80)

    # ファイル読み込み
    files = {
        "White": "TEMPLATE_SolidFill_White.prtextstyle",
        "Red": "赤・ストローク無し.prtextstyle",
        "Blue": "青・ストローク無し.prtextstyle",
        "WhiteStroke": "TEMPLATE_SolidFill_White_StrokeBlack.prtextstyle",
    }

    binaries = {}
    for name, filepath in files.items():
        try:
            binary = extract_binary(filepath)
            if binary:
                binaries[name] = binary
                print(f"✓ {name}: {len(binary)} bytes")
        except Exception as e:
            print(f"✗ {name}: エラー - {e}")

    if not binaries:
        print("バイナリデータが見つかりませんでした")
        return

    # 各ファイルでRGBパターンを探す
    for name, binary in binaries.items():
        find_rgb_patterns(binary, name)

    # 特定オフセットの比較
    compare_specific_offsets(binaries)

    # 最後に、バイナリ全体をダンプ（最初の512バイト）
    print("\n\n" + "="*80)
    print("全バイナリダンプ（最初の512バイト）")
    print("="*80)

    for name in ["White", "Red", "Blue"]:
        if name not in binaries:
            continue

        print(f"\n[{name}]")
        binary = binaries[name]

        for i in range(0, min(len(binary), 512), 16):
            chunk = binary[i:i+16]
            hex_part = ' '.join(f'{b:02x}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            print(f"{i:04x}:  {hex_part:<48}  {ascii_part}")

    print("\n" + "="*80)
    print("✅ 解析完了")
    print("="*80)

if __name__ == "__main__":
    main()
