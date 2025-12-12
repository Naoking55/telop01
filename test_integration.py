#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合テスト: prsl_converter_modern.py が stylelist 形式を正しく読み込めるか確認
"""

import sys
import os

# prsl_converter_modern.py から parse_prsl をインポート
sys.path.insert(0, '/home/user/telop01')

print("=" * 70)
print("PRSL Converter Integration Test")
print("=" * 70)

print("\n[1] Importing parse_prsl from prsl_converter_modern...")
try:
    from prsl_converter_modern import parse_prsl
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# テストファイル
test_files = [
    "テスト1.prsl",
    "10styles.prsl",
]

print("\n[2] Testing PRSL file parsing...")
for filename in test_files:
    if not os.path.exists(filename):
        print(f"⚠ {filename} not found, skipping")
        continue

    print(f"\n  Testing: {filename}")
    try:
        styles = parse_prsl(filename)
        print(f"  ✓ Parsed {len(styles)} styles")

        if styles:
            # 最初のスタイルの詳細を表示
            s = styles[0]
            print(f"    First style: {s.name}")
            print(f"    Font: {s.font_family} ({s.font_size}pt)")
            print(f"    Fill: {s.fill.fill_type}")
            if s.fill.fill_type == "solid":
                print(f"    Fill color: RGB({s.fill.r}, {s.fill.g}, {s.fill.b})")
            elif s.fill.fill_type == "gradient":
                print(f"    Gradient: {len(s.fill.gradient_stops)} stops")
            print(f"    Strokes: {len(s.strokes)}")
            print(f"    Shadow: {'ON' if s.shadow.enabled else 'OFF'}")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("✅ Integration test completed!")
print("=" * 70)
