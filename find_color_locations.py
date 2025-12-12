#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
色の値の位置を特定する
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

def find_differences(bin1: bytes, bin2: bytes) -> list:
    """2つのバイナリの差分箇所を返す"""
    diffs = []
    min_len = min(len(bin1), len(bin2))

    i = 0
    while i < min_len:
        if bin1[i] != bin2[i]:
            # 差分の開始
            start = i
            while i < min_len and bin1[i] != bin2[i]:
                i += 1
            diffs.append((start, i))
        else:
            i += 1

    return diffs

def main():
    print("="*80)
    print("色の値の位置特定")
    print("="*80)

    # ファイル読み込み
    files = {
        "White": "TEMPLATE_SolidFill_White.prtextstyle",
        "Red": "赤・ストローク無し.prtextstyle",
        "Blue": "青・ストローク無し.prtextstyle",
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

    if len(binaries) < 2:
        print("比較するファイルが不足しています")
        return

    # WhiteとRedの差分
    print("\n" + "="*80)
    print("White vs Red の差分箇所")
    print("="*80)

    white = binaries["White"]
    red = binaries["Red"]

    diffs = find_differences(white, red)

    for start, end in diffs:
        length = end - start
        print(f"\n0x{start:04x}-0x{end:04x} ({length} bytes):")

        # 16バイト単位で表示
        for offset in range(start, min(end, start + 64), 16):
            chunk_len = min(16, end - offset)

            white_chunk = white[offset:offset+chunk_len]
            red_chunk = red[offset:offset+chunk_len] if offset < len(red) else b""

            white_hex = ' '.join(f'{b:02x}' for b in white_chunk)
            red_hex = ' '.join(f'{b:02x}' for b in red_chunk) if red_chunk else ""

            print(f"  0x{offset:04x}:")
            print(f"    White: {white_hex}")
            print(f"    Red:   {red_hex}")

            # float として解釈
            if chunk_len >= 4:
                for i in range(0, chunk_len - 3, 4):
                    try:
                        white_float = struct.unpack("<f", white_chunk[i:i+4])[0]
                        if red_chunk and i + 4 <= len(red_chunk):
                            red_float = struct.unpack("<f", red_chunk[i:i+4])[0]
                            if 0.0 <= white_float <= 1.0 or 0.0 <= red_float <= 1.0:
                                print(f"      +{i:02x} float: {white_float:.6f} vs {red_float:.6f}")
                    except:
                        pass

    # 特定のオフセットを詳細に調査
    print("\n" + "="*80)
    print("重要な差分箇所の詳細分析")
    print("="*80)

    # 0x00b0 付近（White vs Red で差分あり）
    print("\n[0x00b0-0x00c0 付近の詳細]")
    offset = 0x00b0
    for name, binary in binaries.items():
        chunk = binary[offset:offset+32]
        print(f"\n{name}:")
        print(f"  Hex: {chunk.hex()}")

        # 4バイトずつfloatとして解釈
        print(f"  Floats:")
        for i in range(0, min(32, len(chunk)), 4):
            if i + 4 <= len(chunk):
                try:
                    f = struct.unpack("<f", chunk[i:i+4])[0]
                    print(f"    0x{offset+i:04x}: {f:.6f}")
                except:
                    pass

    # WhiteとBlueの差分
    print("\n\n" + "="*80)
    print("White vs Blue の差分箇所")
    print("="*80)

    if "Blue" in binaries:
        blue = binaries["Blue"]
        diffs = find_differences(white, blue)

        for start, end in diffs[:5]:  # 最初の5箇所
            length = end - start
            print(f"\n0x{start:04x}-0x{end:04x} ({length} bytes):")

            # 差分データ
            white_data = white[start:end]
            blue_data = blue[start:end] if start < len(blue) else b""

            print(f"  White: {white_data[:32].hex()}")
            print(f"  Blue:  {blue_data[:32].hex()}")

            # float として解釈
            if length >= 16 and length <= 64:
                print("  Float解釈:")
                for i in range(0, min(length, 32), 4):
                    if i + 4 <= len(white_data):
                        try:
                            w_f = struct.unpack("<f", white_data[i:i+4])[0]
                            if blue_data and i + 4 <= len(blue_data):
                                b_f = struct.unpack("<f", blue_data[i:i+4])[0]
                                print(f"    +{i:02x}: White={w_f:.6f}, Blue={b_f:.6f}")
                        except:
                            pass

    print("\n" + "="*80)
    print("✅ 解析完了")
    print("="*80)

if __name__ == "__main__":
    main()
