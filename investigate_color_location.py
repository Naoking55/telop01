#!/usr/bin/env python3
"""
0x0193と0x0197付近のFill色格納位置を詳しく調査
"""

import sys
sys.path.insert(0, '/home/user/telop01')

from test_prsl_conversion import parse_prsl
from prtextstyle_editor import PrtextstyleEditor
import struct

def hex_dump_region(binary, start, length, label=""):
    """指定範囲をhex dump"""
    print(f"\n{label}")
    print("-" * 80)

    for i in range(start, min(start + length, len(binary)), 16):
        # アドレス
        line = f"{i:04x}: "

        # Hex bytes
        hex_part = ""
        for j in range(16):
            if i + j < len(binary):
                byte = binary[i + j]
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

def analyze_color_region(prsl_style, prt_binary, unique_byte_pos):
    """Fill色が格納されている可能性のある領域を解析"""

    print(f"\n{'='*80}")
    print(f"スタイル: {prsl_style.name}")
    print(f"Fill: RGB({prsl_style.fill.r}, {prsl_style.fill.g}, {prsl_style.fill.b})")
    print(f"Unique byte position: 0x{unique_byte_pos:04x}")
    print('='*80)

    # 0x0190付近（前後32バイト）を表示
    hex_dump_region(prt_binary, unique_byte_pos - 16, 48,
                   f"Region around 0x{unique_byte_pos:04x} (±16 bytes)")

    # その位置のバイト値を確認
    byte_value = prt_binary[unique_byte_pos]
    print(f"\nByte at 0x{unique_byte_pos:04x}: {byte_value} (0x{byte_value:02x})")

    # RGB各成分との対応を確認
    print(f"\nRGB components:")
    print(f"  R = {prsl_style.fill.r} (0x{prsl_style.fill.r:02x})")
    print(f"  G = {prsl_style.fill.g} (0x{prsl_style.fill.g:02x})")
    print(f"  B = {prsl_style.fill.b} (0x{prsl_style.fill.b:02x})")

    # 前後のバイトも確認
    print(f"\nBytes around 0x{unique_byte_pos:04x}:")
    for offset in range(-4, 5):
        pos = unique_byte_pos + offset
        if 0 <= pos < len(prt_binary):
            val = prt_binary[pos]
            marker = " <-- HERE" if offset == 0 else ""
            print(f"  0x{pos:04x}: {val:3d} (0x{val:02x}){marker}")

def compare_two_styles():
    """2つのスタイルを比較してFill色の格納パターンを見つける"""

    # PRSL解析
    prsl_styles = parse_prsl("/tmp/10styles.prsl")

    # 手動変換prtextstyle解析
    editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")

    # スタイル1: RGB(0, 114, 255) - G=114が0x0193に
    style1_prsl = prsl_styles[0]
    style1_prt = editor.get_style_binary(list(editor.styles.keys())[0])

    # スタイル2: RGB(255, 0, 126) - B=126が0x0197に
    style2_prsl = prsl_styles[1]
    style2_prt = editor.get_style_binary(list(editor.styles.keys())[1])

    # 各スタイルの解析
    analyze_color_region(style1_prsl, style1_prt, 0x0193)
    analyze_color_region(style2_prsl, style2_prt, 0x0197)

    # 2つのバイナリを並べて比較
    print(f"\n{'='*80}")
    print("2つのスタイルのバイナリ比較（0x0180-0x01a0領域）")
    print('='*80)

    print(f"\nスタイル1: RGB(0, 114, 255)")
    hex_dump_region(style1_prt, 0x0180, 32, "Style 1")

    print(f"\nスタイル2: RGB(255, 0, 126)")
    hex_dump_region(style2_prt, 0x0180, 32, "Style 2")

    # バイトごとの差分
    print(f"\n{'='*80}")
    print("バイトごとの差分（0x0180-0x01a0）")
    print('='*80)

    print(f"Offset  Style1  Style2  Diff")
    print("-" * 40)
    for i in range(0x0180, 0x01a0):
        if i < len(style1_prt) and i < len(style2_prt):
            b1 = style1_prt[i]
            b2 = style2_prt[i]
            diff_marker = " <--" if b1 != b2 else ""
            print(f"0x{i:04x}  {b1:3d}     {b2:3d}     {diff_marker}")

    # もっと広い範囲で3つ目のスタイルも見る
    if len(prsl_styles) > 2:
        print(f"\n{'='*80}")
        print("3番目のスタイルも確認")
        print('='*80)

        style3_prsl = prsl_styles[2]
        style3_prt = editor.get_style_binary(list(editor.styles.keys())[2])

        print(f"Fill: RGB({style3_prsl.fill.r}, {style3_prsl.fill.g}, {style3_prsl.fill.b})")

        # ユニークなバイトを探す
        for component_name, component_value in [("R", style3_prsl.fill.r),
                                                  ("G", style3_prsl.fill.g),
                                                  ("B", style3_prsl.fill.b)]:
            positions = [i for i, x in enumerate(style3_prt) if x == component_value]
            if len(positions) <= 5:  # ユニークっぽい
                print(f"  {component_name}={component_value}: {len(positions)} occurrences at {[f'0x{x:04x}' for x in positions[:5]]}")

        hex_dump_region(style3_prt, 0x0180, 32, "Style 3")

if __name__ == "__main__":
    compare_two_styles()
