#!/usr/bin/env python3
"""
PRSLファイルの色情報を表示
"""

import sys
import xml.etree.ElementTree as ET

def check_prsl_colors(prsl_file):
    """PRSLファイルの色情報を表示（Float値対応）"""
    print("="*60)
    print(f"PRSL色情報チェック: {prsl_file}")
    print("="*60)

    tree = ET.parse(prsl_file)
    root = tree.getroot()

    for i, styleblock in enumerate(root.findall('.//styleblock'), 1):
        name = styleblock.get('name', 'Unknown')

        # Float値形式を試す: <solid_colour><all><red/green/blue>
        solid_colour = styleblock.find('.//solid_colour/all')

        if solid_colour is not None:
            # Float値（0.0-1.0）をByte値（0-255）に変換
            red_elem = solid_colour.find('red')
            green_elem = solid_colour.find('green')
            blue_elem = solid_colour.find('blue')

            if red_elem is not None and green_elem is not None and blue_elem is not None:
                r_float = float(red_elem.text)
                g_float = float(green_elem.text)
                b_float = float(blue_elem.text)

                r = int(r_float * 255)
                g = int(g_float * 255)
                b = int(b_float * 255)

                # 色判定
                if r == 255 and g == 255 and b == 255:
                    status = "⚠️ 白色（色情報なし）"
                else:
                    status = "✓ 色あり"

                print(f"{i:2d}. {name}")
                print(f"    RGB({r}, {g}, {b}) {status}")
            else:
                print(f"{i:2d}. {name}")
                print(f"    ✗ solid_colour要素不完全")
        else:
            # 旧形式も試す: <fill><color rgb="...">
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
