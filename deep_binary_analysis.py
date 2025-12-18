#!/usr/bin/env python3
"""
手動変換prtextstyleの詳細バイナリ解析
Fill色がどこにあるのか徹底的に探す
"""

import sys
sys.path.insert(0, '/home/user/telop01')

from test_prsl_conversion import parse_prsl
from prtextstyle_editor import PrtextstyleEditor
import struct

def hex_dump(binary, offset=0, length=None, highlight_offsets=None):
    """バイナリをhex dumpで表示"""
    if length is None:
        length = len(binary)

    highlight_offsets = highlight_offsets or []

    for i in range(offset, min(offset + length, len(binary)), 16):
        # アドレス
        line = f"{i:04x}: "

        # Hex bytes
        hex_part = ""
        for j in range(16):
            if i + j < len(binary):
                byte = binary[i + j]
                if i + j in highlight_offsets:
                    hex_part += f"\033[91m{byte:02x}\033[0m "  # Red highlight
                else:
                    hex_part += f"{byte:02x} "
            else:
                hex_part += "   "

        line += hex_part

        # ASCII
        line += " "
        for j in range(16):
            if i + j < len(binary):
                byte = binary[i + j]
                if 32 <= byte <= 126:
                    line += chr(byte)
                else:
                    line += "."

        print(line)

def search_all_formats(binary, r, g, b, a=255):
    """あらゆる形式でRGB値を検索"""
    results = {}

    # Format 1: RGB Bytes (0-255)
    print(f"\n[1] RGB Bytes: {r}, {g}, {b}")
    matches = []
    for offset in range(len(binary) - 2):
        if binary[offset] == r and binary[offset+1] == g and binary[offset+2] == b:
            matches.append(offset)
    if matches:
        results['RGB_Bytes'] = matches
        print(f"  ✓ Found at: {[f'0x{x:04x}' for x in matches[:5]]}")
    else:
        print(f"  ✗ Not found")

    # Format 2: RGBA Bytes (0-255)
    print(f"\n[2] RGBA Bytes: {r}, {g}, {b}, {a}")
    matches = []
    for offset in range(len(binary) - 3):
        if binary[offset] == r and binary[offset+1] == g and binary[offset+2] == b and binary[offset+3] == a:
            matches.append(offset)
    if matches:
        results['RGBA_Bytes'] = matches
        print(f"  ✓ Found at: {[f'0x{x:04x}' for x in matches[:5]]}")
    else:
        print(f"  ✗ Not found")

    # Format 3: BGR Bytes (reversed)
    print(f"\n[3] BGR Bytes: {b}, {g}, {r}")
    matches = []
    for offset in range(len(binary) - 2):
        if binary[offset] == b and binary[offset+1] == g and binary[offset+2] == r:
            matches.append(offset)
    if matches:
        results['BGR_Bytes'] = matches
        print(f"  ✓ Found at: {[f'0x{x:04x}' for x in matches[:5]]}")
    else:
        print(f"  ✗ Not found")

    # Format 4: BGRA Bytes (reversed with alpha)
    print(f"\n[4] BGRA Bytes: {b}, {g}, {r}, {a}")
    matches = []
    for offset in range(len(binary) - 3):
        if binary[offset] == b and binary[offset+1] == g and binary[offset+2] == r and binary[offset+3] == a:
            matches.append(offset)
    if matches:
        results['BGRA_Bytes'] = matches
        print(f"  ✓ Found at: {[f'0x{x:04x}' for x in matches[:5]]}")
    else:
        print(f"  ✗ Not found")

    # Format 5: RGBA Float (0.0-1.0)
    print(f"\n[5] RGBA Float: {r/255:.3f}, {g/255:.3f}, {b/255:.3f}, {a/255:.3f}")
    matches = []
    target_r = r / 255.0
    target_g = g / 255.0
    target_b = b / 255.0
    target_a = a / 255.0

    for offset in range(0, len(binary) - 15, 1):
        try:
            fr = struct.unpack('<f', binary[offset:offset+4])[0]
            fg = struct.unpack('<f', binary[offset+4:offset+8])[0]
            fb = struct.unpack('<f', binary[offset+8:offset+12])[0]
            fa = struct.unpack('<f', binary[offset+12:offset+16])[0]

            if (abs(fr - target_r) < 0.01 and abs(fg - target_g) < 0.01 and
                abs(fb - target_b) < 0.01 and abs(fa - target_a) < 0.01):
                matches.append(offset)
        except:
            pass

    if matches:
        results['RGBA_Float'] = matches
        print(f"  ✓ Found at: {[f'0x{x:04x}' for x in matches[:5]]}")
    else:
        print(f"  ✗ Not found")

    # Format 6: Single bytes anywhere
    print(f"\n[6] Individual bytes in binary:")
    print(f"  R={r}: {sum(1 for x in binary if x == r)} occurrences")
    print(f"  G={g}: {sum(1 for x in binary if x == g)} occurrences")
    print(f"  B={b}: {sum(1 for x in binary if x == b)} occurrences")

    # Find positions of individual bytes
    r_positions = [i for i, x in enumerate(binary) if x == r]
    g_positions = [i for i, x in enumerate(binary) if x == g]
    b_positions = [i for i, x in enumerate(binary) if x == b]

    if r_positions:
        print(f"  R positions: {[f'0x{x:04x}' for x in r_positions[:10]]}")
    if g_positions:
        print(f"  G positions: {[f'0x{x:04x}' for x in g_positions[:10]]}")
    if b_positions:
        print(f"  B positions: {[f'0x{x:04x}' for x in b_positions[:10]]}")

    return results

def main():
    print("="*80)
    print("手動変換prtextstyleの詳細バイナリ解析")
    print("="*80)

    # PRSL解析
    prsl_styles = parse_prsl("/tmp/10styles.prsl")

    # 手動変換prtextstyle解析
    editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")

    # 最初のスタイルを解析
    prsl_style = prsl_styles[0]
    prt_style_name = list(editor.styles.keys())[0]
    prt_binary = editor.get_style_binary(prt_style_name)

    print(f"\nスタイル: {prsl_style.name}")
    print(f"Fill: RGB({prsl_style.fill.r}, {prsl_style.fill.g}, {prsl_style.fill.b}, {prsl_style.fill.a})")
    print(f"Binary size: {len(prt_binary)} bytes")

    print(f"\n{'='*80}")
    print("あらゆる形式でFill色を検索")
    print('='*80)

    results = search_all_formats(
        prt_binary,
        prsl_style.fill.r,
        prsl_style.fill.g,
        prsl_style.fill.b,
        prsl_style.fill.a
    )

    print(f"\n{'='*80}")
    print("バイナリ全体のHex Dump（最初の256バイト）")
    print('='*80)

    # Highlight individual byte positions
    all_highlights = []
    if prsl_style.fill.r in prt_binary[:256]:
        all_highlights.extend([i for i, x in enumerate(prt_binary[:256]) if x == prsl_style.fill.r])
    if prsl_style.fill.g in prt_binary[:256]:
        all_highlights.extend([i for i, x in enumerate(prt_binary[:256]) if x == prsl_style.fill.g])
    if prsl_style.fill.b in prt_binary[:256]:
        all_highlights.extend([i for i, x in enumerate(prt_binary[:256]) if x == prsl_style.fill.b])

    hex_dump(prt_binary, 0, 256, all_highlights)

    # 2番目のスタイルも比較
    if len(prsl_styles) > 1:
        print(f"\n{'='*80}")
        print("2番目のスタイルと比較")
        print('='*80)

        prsl_style2 = prsl_styles[1]
        prt_style_name2 = list(editor.styles.keys())[1]
        prt_binary2 = editor.get_style_binary(prt_style_name2)

        print(f"\nスタイル: {prsl_style2.name}")
        print(f"Fill: RGB({prsl_style2.fill.r}, {prsl_style2.fill.g}, {prsl_style2.fill.b})")
        print(f"Binary size: {len(prt_binary2)} bytes")

        search_all_formats(
            prt_binary2,
            prsl_style2.fill.r,
            prsl_style2.fill.g,
            prsl_style2.fill.b,
            prsl_style2.fill.a
        )

if __name__ == "__main__":
    main()
