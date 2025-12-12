#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接パースのみをテスト（GUI不要）
"""

import sys
import os
from xml.etree import ElementTree as ET

sys.path.insert(0, '/home/user/telop01')

print("=" * 70)
print("PRSL Format Detection & Parsing Test")
print("=" * 70)

# テストファイル
test_files = [
    ("テスト1.prsl", "stylelist"),
    ("10styles.prsl", "stylelist"),
    ("sample_style.prsl", "StyleProjectItem"),  # これはサンプルで従来形式
]

print("\n[1] Testing format detection...")
for filename, expected_format in test_files:
    if not os.path.exists(filename):
        print(f"⚠ {filename} not found, skipping")
        continue

    print(f"\n  File: {filename}")
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        detected_format = root.tag
        print(f"  Detected format: <{detected_format}>")

        if detected_format == expected_format:
            print(f"  ✓ Matches expected format")
        else:
            print(f"  ⚠ Expected <{expected_format}>, got <{detected_format}>")

        # 適切なパーサーを使用
        if detected_format == "stylelist":
            from prsl_parser_stylelist import parse_prsl_stylelist
            styles = parse_prsl_stylelist(filename)
            print(f"  ✓ Parsed {len(styles)} styles using stylelist parser")

            if styles:
                s = styles[0]
                print(f"    - First: {s.name}")
                print(f"    - Font: {s.font_family} ({s.font_size}pt)")
                print(f"    - Fill: {s.fill.fill_type}")
                if s.fill.fill_type == "gradient":
                    print(f"    - Gradient stops: {len(s.fill.gradient_stops)}")

        elif detected_format == "PremiereData":
            # 従来形式 - StyleProjectItem を探す
            style_items = root.findall(".//StyleProjectItem")
            print(f"  Found {len(style_items)} StyleProjectItem elements")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("✅ Format detection test completed!")
print("=" * 70)
print("\nConclusion:")
print("  - stylelist format: Use prsl_parser_stylelist.py")
print("  - StyleProjectItem format: Use original PRSLParser")
