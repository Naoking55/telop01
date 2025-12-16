#!/usr/bin/env python3
"""
PRSLファイルの色情報を表示
"""

import sys
import xml.etree.ElementTree as ET

def check_prsl_colors(prsl_file):
    """PRSLファイルの色情報を表示"""
    print("="*60)
    print(f"PRSL色情報チェック: {prsl_file}")
    print("="*60)

    tree = ET.parse(prsl_file)
    root = tree.getroot()

    for i, styleblock in enumerate(root.findall('.//styleblock'), 1):
        name = styleblock.get('name', 'Unknown')

        fill_elem = styleblock.find('.//fill/color')
        if fill_elem is not None:
            rgb = fill_elem.get('rgb', '255 255 255')
            r, g, b = map(int, rgb.split())

            # 色判定
            if r == 255 and g == 255 and b == 255:
                status = "⚠️ 白色（色情報なし）"
            else:
                status = "✓ 色あり"

            print(f"{i:2d}. {name}")
            print(f"    RGB({r}, {g}, {b}) {status}")
        else:
            print(f"{i:2d}. {name}")
            print(f"    ✗ fill要素なし")

    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python3 check_prsl_colors.py <prsl_file>")
        sys.exit(1)

    check_prsl_colors(sys.argv[1])
