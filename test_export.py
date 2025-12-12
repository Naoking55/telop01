#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エクスポート機能テスト: stylelist形式PRSL → prtextstyle変換
"""

import sys
import os

sys.path.insert(0, '/home/user/telop01')

print("=" * 70)
print("PRSL → prtextstyle Export Test")
print("=" * 70)

# Parse a stylelist format PRSL file
print("\n[1] Parsing PRSL file...")
from prsl_parser_stylelist import parse_prsl_stylelist

test_file = "10styles.prsl"
if not os.path.exists(test_file):
    print(f"✗ {test_file} not found")
    sys.exit(1)

styles = parse_prsl_stylelist(test_file)
print(f"✓ Parsed {len(styles)} styles from {test_file}")

if not styles:
    print("✗ No styles to export")
    sys.exit(1)

# Export first style
print("\n[2] Exporting first style to prtextstyle...")
style = styles[0]
print(f"  Style: {style.name}")
print(f"  Font: {style.font_family} ({style.font_size}pt)")
print(f"  Fill: {style.fill.fill_type}")

# Import export function from the simple test script
from prsl_test_simple import export_prtextstyle

output_file = "test_output.prtextstyle"
try:
    export_prtextstyle(style, output_file)
    print(f"✓ Exported to {output_file}")

    # Verify file exists and has content
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        print(f"  File size: {size} bytes")

        # Check XML structure
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read(500)
            if '<?xml' in content and 'PremiereData' in content:
                print("  ✓ XML structure looks valid")
            else:
                print("  ⚠ XML structure may be invalid")

            # Show preview
            print(f"\n  Preview:")
            print("  " + "-" * 66)
            for line in content.split('\n')[:10]:
                print(f"  {line}")
            print("  " + "-" * 66)

except Exception as e:
    print(f"✗ Export failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ Export test completed!")
print("=" * 70)
print(f"\nGenerated file: {output_file}")
print("You can import this file into Adobe Premiere Pro Essential Graphics")
