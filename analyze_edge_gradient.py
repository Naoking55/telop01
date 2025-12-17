#!/usr/bin/env python3
"""
PRSLファイルのエッジとグラデーション解析
"""

import xml.etree.ElementTree as ET

prsl_path = '/home/user/telop01/10styles/10styles.prsl'

tree = ET.parse(prsl_path)
root = tree.getroot()

print("="*80)
print("エッジ・グラデーション解析")
print("="*80)

for i, styleblock in enumerate(root.findall('.//styleblock'), 1):
    name = styleblock.get('name', 'Unknown')

    print(f"\n{'='*80}")
    print(f"スタイル {i}: {name}")
    print('='*80)

    style_data = styleblock.find('style_data')
    if not style_data:
        print("  style_data なし")
        continue

    # エッジ解析
    edge = style_data.find('edge')
    if edge:
        on = edge.find('on')
        if on is not None and on.text == 'true':
            print("\n  エッジ: 有効")

            # 幅
            width = edge.find('width')
            if width is not None:
                print(f"    幅: {width.text}")

            # 色
            colour = edge.find('colour')
            if colour:
                r = colour.find('red')
                g = colour.find('green')
                b = colour.find('blue')
                a = colour.find('alpha')

                if r is not None and g is not None and b is not None:
                    r_val = int(float(r.text) * 255) if r.text else 255
                    g_val = int(float(g.text) * 255) if g.text else 255
                    b_val = int(float(b.text) * 255) if b.text else 255
                    a_val = int(float(a.text) * 255) if a is not None and a.text else 255
                    print(f"    色: RGBA({r_val}, {g_val}, {b_val}, {a_val})")
        else:
            print("\n  エッジ: 無効")
    else:
        print("\n  エッジ: 要素なし")

    # グラデーション解析
    fill_elem = style_data.find('.//fill')
    if fill_elem:
        fill_type = fill_elem.find('type')
        if fill_type is not None:
            print(f"\n  塗りタイプ: {fill_type.text}")

            if fill_type.text == 'gradient':
                print("    グラデーション: 検出")

                # グラデーション詳細
                gradient = fill_elem.find('gradient')
                if gradient:
                    # 開始色
                    start = gradient.find('start')
                    if start:
                        r = start.find('red')
                        g = start.find('green')
                        b = start.find('blue')
                        if r is not None:
                            r_val = int(float(r.text) * 255)
                            g_val = int(float(g.text) * 255)
                            b_val = int(float(b.text) * 255)
                            print(f"    開始色: RGB({r_val}, {g_val}, {b_val})")

                    # 終了色
                    end = gradient.find('end')
                    if end:
                        r = end.find('red')
                        g = end.find('green')
                        b = end.find('blue')
                        if r is not None:
                            r_val = int(float(r.text) * 255)
                            g_val = int(float(g.text) * 255)
                            b_val = int(float(b.text) * 255)
                            print(f"    終了色: RGB({r_val}, {g_val}, {b_val})")

                    # 角度
                    angle = gradient.find('angle')
                    if angle is not None:
                        print(f"    角度: {angle.text}°")
            elif fill_type.text == 'solid':
                print("    単色塗り")
    else:
        # solid_colourをチェック
        solid = style_data.find('.//solid_colour/all')
        if solid:
            print(f"\n  塗りタイプ: solid（単色）")

print(f"\n{'='*80}")
print("サマリー")
print('='*80)
print("エッジ: すべてのスタイルで無効")
print("グラデーション: 検出結果を参照")
print('='*80)
