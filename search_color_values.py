#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
色の値を全形式で探索
"""

from xml.etree import ElementTree as ET
import base64
import struct

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

def search_value_all_formats(binary: bytes, name: str, target_values: list):
    """
    様々な形式で値を探す
    target_values: [(値, 説明), ...]の形式
    """
    print(f"\n{'='*80}")
    print(f"{name} での値の探索")
    print(f"{'='*80}")

    for target, description in target_values:
        print(f"\n[{description}: {target}]")

        # Float (0.0-1.0)
        if 0.0 <= target <= 1.0:
            target_bytes = struct.pack("<f", target)
            for i in range(len(binary) - 3):
                if binary[i:i+4] == target_bytes:
                    print(f"  Float 0x{i:04x}: {target:.6f}")

        # Float (0-255スケール)
        target_255 = target
        target_bytes_255 = struct.pack("<f", target_255)
        for i in range(len(binary) - 3):
            if binary[i:i+4] == target_bytes_255:
                print(f"  Float(0-255) 0x{i:04x}: {target_255:.6f}")

        # Byte
        if 0 <= target <= 255:
            target_int = int(target)
            for i in range(len(binary)):
                if binary[i] == target_int:
                    print(f"  Byte 0x{i:04x}: {target_int}")

        # 16bit unsigned
        if 0 <= target <= 65535:
            target_int = int(target)
            target_bytes_u16 = struct.pack("<H", target_int)
            for i in range(len(binary) - 1):
                if binary[i:i+2] == target_bytes_u16:
                    print(f"  UInt16 0x{i:04x}: {target_int}")

        # 32bit unsigned
        if 0 <= target <= 4294967295:
            target_int = int(target)
            target_bytes_u32 = struct.pack("<I", target_int)
            for i in range(len(binary) - 3):
                if binary[i:i+4] == target_bytes_u32:
                    print(f"  UInt32 0x{i:04x}: {target_int}")

def compare_byte_by_byte(binaries: dict):
    """バイト単位で比較して、色に関連しそうな差分を見つける"""
    print("\n" + "="*80)
    print("バイト単位での比較")
    print("="*80)

    white = binaries.get("White", b"")
    red = binaries.get("Red", b"")
    blue = binaries.get("Blue", b"")

    min_len = min(len(white), len(red), len(blue))

    print("\nWhite vs Red vs Blue の差分:")
    print("(White, Red, Blue が全て異なる箇所)")

    diff_regions = []
    i = 0
    while i < min_len:
        if white[i] != red[i] or white[i] != blue[i] or red[i] != blue[i]:
            # 差分の開始
            start = i
            while i < min_len and (white[i] != red[i] or white[i] != blue[i] or red[i] != blue[i]):
                i += 1
            diff_regions.append((start, i))
        else:
            i += 1

    for start, end in diff_regions[:20]:  # 最初の20箇所
        print(f"\n0x{start:04x}-0x{end:04x} ({end-start} bytes):")

        # 各ファイルの値
        w_chunk = white[start:end]
        r_chunk = red[start:end]
        b_chunk = blue[start:end]

        print(f"  White: {w_chunk[:16].hex()}")
        print(f"  Red:   {r_chunk[:16].hex()}")
        print(f"  Blue:  {b_chunk[:16].hex()}")

        # float解釈
        if len(w_chunk) >= 4:
            try:
                w_f = struct.unpack("<f", w_chunk[:4])[0]
                r_f = struct.unpack("<f", r_chunk[:4])[0]
                b_f = struct.unpack("<f", b_chunk[:4])[0]
                if all(-10.0 <= f <= 300.0 for f in [w_f, r_f, b_f]):
                    print(f"  Float: White={w_f:.3f}, Red={r_f:.3f}, Blue={b_f:.3f}")
            except:
                pass

def main():
    print("="*80)
    print("色の値の全形式探索")
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

    if len(binaries) < 3:
        print("ファイルが不足しています")
        return

    # 期待される色の値を探す
    # 白: RGB(255, 255, 255) = (1.0, 1.0, 1.0)
    # 赤: RGB(255, 0, 0) = (1.0, 0.0, 0.0)
    # 青: RGB(0, 0, 255) = (0.0, 0.0, 1.0)

    # Whiteファイルで1.0を探す
    search_value_all_formats(binaries["White"], "White", [
        (1.0, "白のR成分 (float 1.0)"),
        (255, "白のR成分 (int 255)"),
        (0.0, "他の成分 (float 0.0)"),
    ])

    # Redファイルで1.0と0.0を探す
    search_value_all_formats(binaries["Red"], "Red", [
        (1.0, "赤のR成分 (float 1.0)"),
        (0.0, "赤のG/B成分 (float 0.0)"),
        (255, "赤のR成分 (int 255)"),
        (0, "赤のG/B成分 (int 0)"),
    ])

    # Blueファイルで1.0と0.0を探す
    search_value_all_formats(binaries["Blue"], "Blue", [
        (1.0, "青のB成分 (float 1.0)"),
        (0.0, "青のR/G成分 (float 0.0)"),
        (255, "青のB成分 (int 255)"),
        (0, "青のR/G成分 (int 0)"),
    ])

    # バイト単位比較
    compare_byte_by_byte(binaries)

    print("\n" + "="*80)
    print("✅ 探索完了")
    print("="*80)

if __name__ == "__main__":
    main()
