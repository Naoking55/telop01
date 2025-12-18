#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
レンダリングテスト: スタイルのプレビュー画像生成
"""

import sys
import os

sys.path.insert(0, '/home/user/telop01')

print("=" * 70)
print("Style Rendering Test")
print("=" * 70)

# Parse styles
print("\n[1] Parsing PRSL file...")
from prsl_parser_stylelist import parse_prsl_stylelist

test_file = "10styles.prsl"
styles = parse_prsl_stylelist(test_file)
print(f"✓ Parsed {len(styles)} styles")

# Render first few styles
print("\n[2] Rendering styles...")
from prsl_test_simple import render_style

output_files = []
for i, style in enumerate(styles[:3], 1):  # First 3 styles
    print(f"\n  Style {i}: {style.name}")
    try:
        # Render
        img = render_style("テスト", style, canvas_size=(600, 200))

        # Save
        output_file = f"test_output_{i}.png"
        img.save(output_file)
        output_files.append(output_file)

        print(f"  ✓ Rendered and saved to {output_file}")
        print(f"    Size: {img.size[0]}x{img.size[1]}")

    except Exception as e:
        print(f"  ✗ Rendering failed: {e}")

print("\n" + "=" * 70)
print("✅ Rendering test completed!")
print("=" * 70)

if output_files:
    print(f"\nGenerated {len(output_files)} preview images:")
    for f in output_files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"  📷 {f} ({size} bytes)")
