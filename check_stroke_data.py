#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ストロークデータの確認
"""

import sys
sys.path.insert(0, '/home/user/telop01')

from prsl_parser_stylelist import parse_prsl_stylelist

print("=" * 70)
print("ストロークデータの詳細確認")
print("=" * 70)

test_file = "10styles.prsl"
styles = parse_prsl_stylelist(test_file)

for i, style in enumerate(styles[:5], 1):
    print(f"\n{'='*70}")
    print(f"スタイル {i}: {style.name}")
    print(f"{'='*70}")
    print(f"フォント: {style.font_family} ({style.font_size}pt)")
    print(f"塗り: {style.fill.fill_type}")
    if style.fill.fill_type == "solid":
        print(f"  色: RGB({style.fill.r}, {style.fill.g}, {style.fill.b}, {style.fill.a})")
    else:
        print(f"  グラデーション: {len(style.fill.gradient_stops)} stops")

    print(f"\nストローク数: {len(style.strokes)}")
    if style.strokes:
        for j, stroke in enumerate(style.strokes, 1):
            print(f"  ストローク {j}:")
            print(f"    幅: {stroke.width}")
            print(f"    色: RGB({stroke.r}, {stroke.g}, {stroke.b}, {stroke.a})")
    else:
        print("  ストロークなし")

    print(f"\nシャドウ: {style.shadow.enabled}")
    if style.shadow.enabled:
        print(f"  オフセット: ({style.shadow.offset_x}, {style.shadow.offset_y})")
        print(f"  ぼかし: {style.shadow.blur}")
        print(f"  色: RGB({style.shadow.r}, {style.shadow.g}, {style.shadow.b}, {style.shadow.a})")
