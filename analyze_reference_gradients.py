#!/usr/bin/env python3
"""
参考スタイル.prsl のグラデーション解析
"""

import xml.etree.ElementTree as ET

prsl_path = '10styles/参考スタイル.prsl'

tree = ET.parse(prsl_path)
root = tree.getroot()

print("="*80)
print("グラデーションスタイル一覧")
print("="*80)

gradient_styles = []

for i, styleblock in enumerate(root.findall('.//styleblock'), 1):
    name = styleblock.get('name', 'Unknown')
    sd = styleblock.find('style_data')

    if not sd:
        continue

    colouring = sd.find('.//face/shader/colouring')
    if colouring:
        fill_type_elem = colouring.find('type')
        if fill_type_elem is not None:
            fill_type = int(fill_type_elem.text.strip())

            # グラデーション（タイプ1または2）
            if fill_type in [1, 2]:
                gradient_styles.append((i, name, fill_type))

                print(f"\nスタイル {i}: {name}")
                print(f"  タイプ: {fill_type} ({'4色' if fill_type == 1 else '2色'}グラデーション)")

                if fill_type == 1:  # 4色グラデーション
                    ramp = colouring.find('four_colour_ramp')
                    if ramp:
                        tl = ramp.find('top_left')
                        br = ramp.find('bottom_right')
                        if tl and br:
                            r1 = int(float(tl.find('red').text) * 255)
                            g1 = int(float(tl.find('green').text) * 255)
                            b1 = int(float(tl.find('blue').text) * 255)
                            r2 = int(float(br.find('red').text) * 255)
                            g2 = int(float(br.find('green').text) * 255)
                            b2 = int(float(br.find('blue').text) * 255)
                            print(f"  上: RGB({r1}, {g1}, {b1})")
                            print(f"  下: RGB({r2}, {g2}, {b2})")

                elif fill_type == 2:  # 2色グラデーション
                    ramp = colouring.find('two_colour_ramp')
                    if ramp:
                        top = ramp.find('top')
                        bottom = ramp.find('bottom')
                        if top and bottom:
                            r1 = int(float(top.find('red').text) * 255)
                            g1 = int(float(top.find('green').text) * 255)
                            b1 = int(float(top.find('blue').text) * 255)
                            r2 = int(float(bottom.find('red').text) * 255)
                            g2 = int(float(bottom.find('green').text) * 255)
                            b2 = int(float(bottom.find('blue').text) * 255)
                            print(f"  開始: RGB({r1}, {g1}, {b1})")
                            print(f"  終了: RGB({r2}, {g2}, {b2})")

                            angle = ramp.find('angle')
                            if angle is not None:
                                print(f"  角度: {angle.text}°")

print(f"\n{'='*80}")
print(f"合計: {len(gradient_styles)}個のグラデーションスタイル")
print('='*80)
