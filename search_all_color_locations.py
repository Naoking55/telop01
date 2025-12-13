#!/usr/bin/env python3
"""
Fill色の全ての格納位置を探す
バイナリ全体を徹底的に調査
"""

import sys
sys.path.insert(0, '/home/user/telop01')

from test_prsl_conversion import parse_prsl
from prtextstyle_editor import PrtextstyleEditor
import struct

def search_all_color_formats(binary, r, g, b, label=""):
    """全ての可能な形式で色を探す"""
    results = []

    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"Searching for RGB({r}, {g}, {b}) in all formats")
    print('='*80)

    # Format 1: RGB Bytes
    print(f"\n[1] RGB Bytes sequence: [{r}, {g}, {b}]")
    for offset in range(len(binary) - 2):
        if binary[offset] == r and binary[offset+1] == g and binary[offset+2] == b:
            print(f"  ✓ Found at 0x{offset:04x}")
            results.append(('RGB', offset))

    # Format 2: RGBA Bytes (with various alpha values)
    print(f"\n[2] RGBA Bytes sequence: [{r}, {g}, {b}, ?]")
    for offset in range(len(binary) - 3):
        if binary[offset] == r and binary[offset+1] == g and binary[offset+2] == b:
            alpha = binary[offset+3]
            print(f"  ✓ Found at 0x{offset:04x} (alpha={alpha})")
            results.append(('RGBA', offset))

    # Format 3: BGR Bytes (reversed)
    print(f"\n[3] BGR Bytes sequence: [{b}, {g}, {r}]")
    for offset in range(len(binary) - 2):
        if binary[offset] == b and binary[offset+1] == g and binary[offset+2] == r:
            print(f"  ✓ Found at 0x{offset:04x}")
            results.append(('BGR', offset))

    # Format 4: BGRA Bytes
    print(f"\n[4] BGRA Bytes sequence: [{b}, {g}, {r}, ?]")
    for offset in range(len(binary) - 3):
        if binary[offset] == b and binary[offset+1] == g and binary[offset+2] == r:
            alpha = binary[offset+3]
            print(f"  ✓ Found at 0x{offset:04x} (alpha={alpha})")
            results.append(('BGRA', offset))

    # Format 5: Individual bytes anywhere
    print(f"\n[5] Individual component bytes:")
    r_positions = [i for i, x in enumerate(binary) if x == r]
    g_positions = [i for i, x in enumerate(binary) if x == g]
    b_positions = [i for i, x in enumerate(binary) if x == b]

    print(f"  R={r}: {len(r_positions)} occurrences")
    if len(r_positions) <= 20:
        print(f"    Positions: {[f'0x{x:04x}' for x in r_positions]}")

    print(f"  G={g}: {len(g_positions)} occurrences")
    if len(g_positions) <= 20:
        print(f"    Positions: {[f'0x{x:04x}' for x in g_positions]}")

    print(f"  B={b}: {len(b_positions)} occurrences")
    if len(b_positions) <= 20:
        print(f"    Positions: {[f'0x{x:04x}' for x in b_positions]}")

    # Format 6: RGBA Float
    print(f"\n[6] RGBA Float: [{r/255:.3f}, {g/255:.3f}, {b/255:.3f}, ?]")
    target_r = r / 255.0
    target_g = g / 255.0
    target_b = b / 255.0

    for offset in range(0, len(binary) - 11, 1):
        try:
            fr = struct.unpack('<f', binary[offset:offset+4])[0]
            fg = struct.unpack('<f', binary[offset+4:offset+8])[0]
            fb = struct.unpack('<f', binary[offset+8:offset+12])[0]

            if abs(fr - target_r) < 0.01 and abs(fg - target_g) < 0.01 and abs(fb - target_b) < 0.01:
                if len(binary) >= offset + 16:
                    fa = struct.unpack('<f', binary[offset+12:offset+16])[0]
                    print(f"  ✓ Found at 0x{offset:04x} (alpha={fa:.3f})")
                else:
                    print(f"  ✓ Found at 0x{offset:04x}")
                results.append(('RGBA_Float', offset))
        except:
            pass

    if not results:
        print("\n✗ No color sequences found in any format!")

    return results

def compare_two_similar_colors():
    """
    2つの似た色のスタイルを比較して、色以外は同じ部分と色で異なる部分を見つける
    """

    print("="*80)
    print("2つのスタイルを比較して色の格納位置を特定")
    print("="*80)

    # PRSL解析
    prsl_styles = parse_prsl("/tmp/10styles.prsl")

    # 手動変換prtextstyle解析
    editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")

    # Style 1と2を比較（両方ともサイズは近い）
    style1_prsl = prsl_styles[0]  # RGB(0, 114, 255)
    style1_prt = editor.get_style_binary(list(editor.styles.keys())[0])

    style2_prsl = prsl_styles[1]  # RGB(255, 0, 126)
    style2_prt = editor.get_style_binary(list(editor.styles.keys())[1])

    print(f"\nStyle 1: RGB({style1_prsl.fill.r}, {style1_prsl.fill.g}, {style1_prsl.fill.b})")
    print(f"  Binary size: {len(style1_prt)} bytes")

    print(f"\nStyle 2: RGB({style2_prsl.fill.r}, {style2_prsl.fill.g}, {style2_prsl.fill.b})")
    print(f"  Binary size: {len(style2_prt)} bytes")

    # Style 1の色を全検索
    search_all_color_formats(style1_prt, style1_prsl.fill.r, style1_prsl.fill.g, style1_prsl.fill.b,
                            "Style 1 Color Search")

    # Style 2の色を全検索
    search_all_color_formats(style2_prt, style2_prsl.fill.r, style2_prsl.fill.g, style2_prsl.fill.b,
                            "Style 2 Color Search")

    # さらに、RGB(100, 200, 255)のような中間的な色がどこかにあるか探す
    print(f"\n{'='*80}")
    print("Test: もし RGB(100, 200, 255) が Style 1 のバイナリにあったら？")
    print('='*80)
    search_all_color_formats(style1_prt, 100, 200, 255, "Testing RGB(100, 200, 255) in Style 1")

if __name__ == "__main__":
    compare_two_similar_colors()
