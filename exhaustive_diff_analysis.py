#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
White/Red/Blue の完全な差分解析
全てのバイト、全ての可能性を調査
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

def interpret_as_all_types(data: bytes, offset: int) -> dict:
    """4バイトを全ての型として解釈"""
    if offset + 4 > len(data):
        return {}

    chunk = data[offset:offset+4]
    result = {}

    # Unsigned integers
    result['uint32_le'] = struct.unpack("<I", chunk)[0]
    result['uint32_be'] = struct.unpack(">I", chunk)[0]

    # Signed integers
    result['int32_le'] = struct.unpack("<i", chunk)[0]
    result['int32_be'] = struct.unpack(">i", chunk)[0]

    # Float
    try:
        result['float_le'] = struct.unpack("<f", chunk)[0]
        result['float_be'] = struct.unpack(">f", chunk)[0]
    except:
        result['float_le'] = None
        result['float_be'] = None

    # Bytes
    result['bytes'] = chunk.hex()

    return result

def analyze_all_differences():
    """全ての差分を徹底解析"""

    print("="*80)
    print("White/Red/Blue 完全差分解析")
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

    white = binaries["White"]
    red = binaries["Red"]
    blue = binaries["Blue"]

    # 全ての差分箇所をリストアップ
    print("\n" + "="*80)
    print("差分箇所の完全リスト")
    print("="*80)

    min_len = min(len(white), len(red), len(blue))
    diff_offsets = []

    for i in range(min_len):
        if white[i] != red[i] or white[i] != blue[i] or red[i] != blue[i]:
            diff_offsets.append(i)

    print(f"\n差分バイト数: {len(diff_offsets)} / {min_len} ({len(diff_offsets)*100/min_len:.1f}%)")

    # 連続する差分をグループ化
    diff_regions = []
    if diff_offsets:
        start = diff_offsets[0]
        prev = diff_offsets[0]

        for offset in diff_offsets[1:]:
            if offset > prev + 1:
                diff_regions.append((start, prev + 1))
                start = offset
            prev = offset

        diff_regions.append((start, prev + 1))

    print(f"差分領域数: {len(diff_regions)}")

    # 各差分領域を詳細解析
    print("\n" + "="*80)
    print("各差分領域の詳細解析")
    print("="*80)

    for idx, (start, end) in enumerate(diff_regions, 1):
        length = end - start
        print(f"\n{'='*80}")
        print(f"差分領域 #{idx}: 0x{start:04x}-0x{end:04x} ({length} bytes)")
        print(f"{'='*80}")

        # Hexダンプ
        print("\nHex:")
        w_hex = white[start:end].hex()
        r_hex = red[start:end].hex()
        b_hex = blue[start:end].hex()

        print(f"  White: {w_hex}")
        print(f"  Red:   {r_hex}")
        print(f"  Blue:  {b_hex}")

        # 4バイト以上なら色々な型として解釈
        if length >= 4:
            print("\n4バイト解釈 (先頭):")

            w_types = interpret_as_all_types(white, start)
            r_types = interpret_as_all_types(red, start)
            b_types = interpret_as_all_types(blue, start)

            for key in ['uint32_le', 'int32_le', 'float_le']:
                w_val = w_types.get(key, '?')
                r_val = r_types.get(key, '?')
                b_val = b_types.get(key, '?')

                # Floatの場合は範囲チェック
                if key == 'float_le':
                    if isinstance(w_val, (int, float)) and isinstance(r_val, (int, float)) and isinstance(b_val, (int, float)):
                        if -1.0 <= w_val <= 300.0 and -1.0 <= r_val <= 300.0 and -1.0 <= b_val <= 300.0:
                            print(f"  {key:12s}: White={w_val:.6f}, Red={r_val:.6f}, Blue={b_val:.6f}")
                else:
                    print(f"  {key:12s}: White={w_val}, Red={r_val}, Blue={b_val}")

        # ASCII解釈
        w_ascii = ''.join(chr(b) if 32 <= b < 127 else '.' for b in white[start:end])
        r_ascii = ''.join(chr(b) if 32 <= b < 127 else '.' for b in red[start:end])
        b_ascii = ''.join(chr(b) if 32 <= b < 127 else '.' for b in blue[start:end])

        if any(c != '.' for c in w_ascii + r_ascii + b_ascii):
            print("\nASCII:")
            print(f"  White: '{w_ascii}'")
            print(f"  Red:   '{r_ascii}'")
            print(f"  Blue:  '{b_ascii}'")

        # 周辺コンテキスト（前後16バイト）
        print("\n周辺コンテキスト:")
        context_start = max(0, start - 16)
        context_end = min(len(white), end + 16)

        print(f"\n  White [{context_start:04x}-{context_end:04x}]:")
        for i in range(context_start, context_end, 16):
            chunk = white[i:i+16]
            hex_part = ' '.join(f'{b:02x}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            marker = " <<<" if start <= i < end else ""
            print(f"    {i:04x}: {hex_part:<48} {ascii_part}{marker}")

    # 特定の値を探す
    print("\n\n" + "="*80)
    print("色関連値の探索")
    print("="*80)

    # RGB(255, 255, 255) = White
    # RGB(255, 0, 0) = Red
    # RGB(0, 0, 255) = Blue

    print("\n[1] 255 (0xff) の出現箇所:")
    for name, binary in [("White", white), ("Red", red), ("Blue", blue)]:
        positions = [i for i in range(len(binary)) if binary[i] == 0xff]
        print(f"  {name}: {len(positions)} 箇所 - {[f'0x{p:04x}' for p in positions[:10]]}")

    print("\n[2] 1.0 (float) の出現箇所:")
    one_float = struct.pack("<f", 1.0)
    for name, binary in [("White", white), ("Red", red), ("Blue", blue)]:
        positions = []
        for i in range(len(binary) - 3):
            if binary[i:i+4] == one_float:
                positions.append(i)
        print(f"  {name}: {len(positions)} 箇所 - {[f'0x{p:04x}' for p in positions[:10]]}")

    print("\n[3] RGB値候補の探索:")

    # White: (255, 255, 255) または (1.0, 1.0, 1.0)
    print("\n  White で (255, 255, 255) パターン:")
    for i in range(len(white) - 2):
        if white[i] == 255 and white[i+1] == 255 and white[i+2] == 255:
            print(f"    0x{i:04x}: ff ff ff")

    # Red: (255, 0, 0) または (1.0, 0.0, 0.0)
    print("\n  Red で (255, 0, 0) パターン:")
    for i in range(len(red) - 2):
        if red[i] == 255 and red[i+1] == 0 and red[i+2] == 0:
            print(f"    0x{i:04x}: ff 00 00")

    # Blue: (0, 0, 255) または (0.0, 0.0, 1.0)
    print("\n  Blue で (0, 0, 255) パターン:")
    for i in range(len(blue) - 2):
        if blue[i] == 0 and blue[i+1] == 0 and blue[i+2] == 255:
            print(f"    0x{i:04x}: 00 00 ff")

    print("\n" + "="*80)
    print("✅ 解析完了")
    print("="*80)

if __name__ == "__main__":
    analyze_all_differences()
