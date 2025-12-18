#!/usr/bin/env python3
"""
全スタイルの塗りタイプとグラデーション情報を解析
"""

import xml.etree.ElementTree as ET

prsl_path = '/home/user/telop01/10styles/10styles.prsl'

tree = ET.parse(prsl_path)
root = tree.getroot()

print("="*80)
print("全スタイルの塗りタイプ解析")
print("="*80)

FILL_TYPES = {
    1: "four_colour_ramp（4色グラデーション）",
    2: "two_colour_ramp（2色グラデーション）",
    3: "two_colour_bevel（ベベル）",
    5: "solid_colour（単色）"
}

for i, styleblock in enumerate(root.findall('.//styleblock'), 1):
    name = styleblock.get('name', 'Unknown')

    print(f"\n{'='*80}")
    print(f"スタイル {i}: {name}")
    print('='*80)

    style_data = styleblock.find('style_data')
    if not style_data:
        continue

    # 塗りタイプを取得
    colouring = style_data.find('.//face/shader/colouring')
    if colouring:
        fill_type_elem = colouring.find('type')
        if fill_type_elem is not None:
            fill_type = int(fill_type_elem.text.strip())
            print(f"\n塗りタイプ: {fill_type} = {FILL_TYPES.get(fill_type, '不明')}")

            # タイプ別の詳細情報
            if fill_type == 5:  # solid_colour
                solid = colouring.find('solid_colour/all')
                if solid:
                    r = float(solid.find('red').text)
                    g = float(solid.find('green').text)
                    b = float(solid.find('blue').text)
                    print(f"  単色: RGB({int(r*255)}, {int(g*255)}, {int(b*255)})")

            elif fill_type == 2:  # two_colour_ramp
                ramp = colouring.find('two_colour_ramp')
                if ramp:
                    # 開始色
                    top = ramp.find('top')
                    if top is not None:
                        r = float(top.find('red').text)
                        g = float(top.find('green').text)
                        b = float(top.find('blue').text)
                        print(f"  開始色: RGB({int(r*255)}, {int(g*255)}, {int(b*255)})")

                    # 終了色
                    bottom = ramp.find('bottom')
                    if bottom is not None:
                        r = float(bottom.find('red').text)
                        g = float(bottom.find('green').text)
                        b = float(bottom.find('blue').text)
                        print(f"  終了色: RGB({int(r*255)}, {int(g*255)}, {int(b*255)})")

                    # 角度
                    angle = ramp.find('angle')
                    if angle is not None:
                        print(f"  角度: {angle.text}°")

                    # 開始・終了位置
                    top_start = ramp.find('top_start')
                    bottom_start = ramp.find('bottom_start')
                    if top_start is not None and bottom_start is not None:
                        print(f"  開始位置: {top_start.text}%")
                        print(f"  終了位置: {bottom_start.text}%")

                    # 繰り返し
                    repeat = ramp.find('repeat')
                    if repeat is not None:
                        print(f"  繰り返し: {repeat.text}")

                    # 放射状
                    radial = ramp.find('radial')
                    if radial is not None:
                        print(f"  放射状: {radial.text}")

            elif fill_type == 1:  # four_colour_ramp
                ramp = colouring.find('four_colour_ramp')
                if ramp:
                    print(f"  4色グラデーション:")
                    for corner in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
                        corner_elem = ramp.find(corner)
                        if corner_elem is not None:
                            r = float(corner_elem.find('red').text)
                            g = float(corner_elem.find('green').text)
                            b = float(corner_elem.find('blue').text)
                            print(f"    {corner}: RGB({int(r*255)}, {int(g*255)}, {int(b*255)})")

            elif fill_type == 3:  # two_colour_bevel
                bevel = colouring.find('two_colour_bevel')
                if bevel:
                    print(f"  ベベル:")

                    # トップ色
                    top = bevel.find('top')
                    if top is not None:
                        r = float(top.find('red').text)
                        g = float(top.find('green').text)
                        b = float(top.find('blue').text)
                        print(f"    トップ: RGB({int(r*255)}, {int(g*255)}, {int(b*255)})")

                    # ボトム色
                    bottom = bevel.find('bottom')
                    if bottom is not None:
                        r = float(bottom.find('red').text)
                        g = float(bottom.find('green').text)
                        b = float(bottom.find('blue').text)
                        print(f"    ボトム: RGB({int(r*255)}, {int(g*255)}, {int(b*255)})")

                    # サイズ
                    size = bevel.find('size')
                    if size is not None:
                        print(f"    サイズ: {size.text}")

print(f"\n{'='*80}")
print("サマリー")
print('='*80)
print("全スタイルの塗りタイプを確認しました")
print('='*80)
