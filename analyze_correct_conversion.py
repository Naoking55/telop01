#!/usr/bin/env python3
"""
正解ファイルの解析
PRSLと手動変換したprtextstyleを比較して、変換パターンを特定
"""

import sys
sys.path.insert(0, '/home/user/telop01')

from test_prsl_conversion import parse_prsl
from prtextstyle_editor import PrtextstyleEditor
import struct

print("="*80)
print("正解ファイル解析：PRSLと手動変換prtextstyleの比較")
print("="*80)

# PRSL解析
print("\n[1] PRSL解析")
prsl_styles = parse_prsl("/tmp/10styles.prsl")
print(f"  ✓ {len(prsl_styles)}個のスタイルを解析")

# 手動変換prtextstyle解析
print("\n[2] 手動変換prtextstyle解析")
editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")
print(f"  ✓ {len(editor.styles)}個のスタイルを取得")

# 最初のスタイルを詳細比較
if prsl_styles and editor.styles:
    prsl_style = prsl_styles[0]
    prt_style_name = list(editor.styles.keys())[0]
    prt_binary = editor.get_style_binary(prt_style_name)

    print(f"\n{'='*80}")
    print(f"スタイル1の詳細比較")
    print('='*80)

    print(f"\n[PRSL] {prsl_style.name}")
    print(f"  Fill: RGB({prsl_style.fill.r}, {prsl_style.fill.g}, {prsl_style.fill.b}, {prsl_style.fill.a})")
    if prsl_style.shadow.enabled:
        print(f"  Shadow: X={prsl_style.shadow.offset_x:.1f}, Y={prsl_style.shadow.offset_y:.1f}, Blur={prsl_style.shadow.blur:.1f}")

    print(f"\n[prtextstyle] {prt_style_name}")
    print(f"  バイナリサイズ: {len(prt_binary)} bytes")

    # PRSLの色がバイナリのどこにあるか探す
    print(f"\n[検索] PRSL Fill色 RGB({prsl_style.fill.r}, {prsl_style.fill.g}, {prsl_style.fill.b}) を探索...")

    # RGB Bytes形式で探す
    print(f"\n  RGB Bytes形式:")
    found_count = 0
    for offset in range(0, len(prt_binary) - 2):
        r = prt_binary[offset]
        g = prt_binary[offset+1]
        b = prt_binary[offset+2]

        if r == prsl_style.fill.r and g == prsl_style.fill.g and b == prsl_style.fill.b:
            print(f"    ✓ 0x{offset:04x}: RGB({r}, {g}, {b})")
            found_count += 1
            if found_count >= 5:  # 最初の5個だけ
                break

    if found_count == 0:
        print(f"    ✗ RGB Bytes形式では見つかりませんでした")

    # RGBA Float形式で探す
    print(f"\n  RGBA Float形式:")
    target_r = prsl_style.fill.r / 255.0
    target_g = prsl_style.fill.g / 255.0
    target_b = prsl_style.fill.b / 255.0
    target_a = prsl_style.fill.a / 255.0

    found_count = 0
    for offset in range(0, len(prt_binary) - 15, 1):
        try:
            r = struct.unpack('<f', prt_binary[offset:offset+4])[0]
            g = struct.unpack('<f', prt_binary[offset+4:offset+8])[0]
            b = struct.unpack('<f', prt_binary[offset+8:offset+12])[0]
            a = struct.unpack('<f', prt_binary[offset+12:offset+16])[0]

            if (abs(r - target_r) < 0.01 and abs(g - target_g) < 0.01 and
                abs(b - target_b) < 0.01 and abs(a - target_a) < 0.01):
                print(f"    ✓ 0x{offset:04x}: RGBA({r:.3f}, {g:.3f}, {b:.3f}, {a:.3f})")
                found_count += 1
                if found_count >= 5:
                    break
        except:
            pass

    if found_count == 0:
        print(f"    ✗ RGBA Float形式では見つかりませんでした")

    # Shadow検索
    if prsl_style.shadow.enabled:
        print(f"\n[検索] Shadow X={prsl_style.shadow.offset_x:.1f}, Y={prsl_style.shadow.offset_y:.1f} を探索...")
        found_count = 0
        for offset in range(0, len(prt_binary) - 7, 1):
            try:
                x = struct.unpack('<f', prt_binary[offset:offset+4])[0]
                y = struct.unpack('<f', prt_binary[offset+4:offset+8])[0]

                if abs(x - prsl_style.shadow.offset_x) < 0.1 and abs(y - prsl_style.shadow.offset_y) < 0.1:
                    print(f"    ✓ 0x{offset:04x}: Shadow X={x:.2f}, Y={y:.2f}")
                    found_count += 1
                    if found_count >= 3:
                        break
            except:
                pass

        if found_count == 0:
            print(f"    ✗ Shadow X,Yが見つかりませんでした")

print(f"\n{'='*80}")
print("解析完了")
print('='*80)
