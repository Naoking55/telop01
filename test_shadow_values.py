#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シャドウ値の確認
パースされたスタイルのシャドウ情報を詳しく表示
"""

import sys
sys.path.insert(0, '/home/user/telop01')

from prsl_parser_stylelist import parse_prsl_stylelist

test_file = "10styles.prsl"
styles = parse_prsl_stylelist(test_file)

print("=" * 70)
print("シャドウ情報の詳細確認")
print("=" * 70)

for i, style in enumerate(styles[:3], 1):
    print(f"\nスタイル {i}: {style.name}")
    print(f"  フォント: {style.font_family} ({style.font_size}pt)")
    print(f"  塗り: {style.fill.fill_type}")
    if style.fill.fill_type == "solid":
        print(f"    色: RGB({style.fill.r}, {style.fill.g}, {style.fill.b}, {style.fill.a})")

    print(f"\n  シャドウ:")
    print(f"    有効: {style.shadow.enabled}")
    print(f"    オフセットX: {style.shadow.offset_x}")
    print(f"    オフセットY: {style.shadow.offset_y}")
    print(f"    ぼかし: {style.shadow.blur}")
    print(f"    色: RGB({style.shadow.r}, {style.shadow.g}, {style.shadow.b}, {style.shadow.a})")
