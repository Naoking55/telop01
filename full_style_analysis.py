#!/usr/bin/env python3
"""
全スタイルの完全解析：塗り・シャドウ・エンベリッシュメント
"""

import xml.etree.ElementTree as ET

prsl_path = '/home/user/telop01/10styles/10styles.prsl'

tree = ET.parse(prsl_path)
root = tree.getroot()

FILL_TYPES = {
    1: "4色グラデーション",
    2: "2色グラデーション",
    3: "ベベル",
    5: "単色"
}

print("="*80)
print("全スタイル完全解析")
print("="*80)

for i, styleblock in enumerate(root.findall('.//styleblock'), 1):
    name = styleblock.get('name', 'Unknown')
    sd = styleblock.find('style_data')

    if not sd:
        continue

    print(f"\n{'='*80}")
    print(f"スタイル {i}: {name}")
    print('='*80)

    # 1. 塗りタイプ
    colouring = sd.find('.//face/shader/colouring')
    if colouring:
        fill_type_elem = colouring.find('type')
        if fill_type_elem is not None:
            fill_type = int(fill_type_elem.text.strip())
            print(f"\n[塗り] タイプ: {FILL_TYPES.get(fill_type, '不明')}")

            if fill_type == 1:  # 4色グラデーション
                ramp = colouring.find('four_colour_ramp')
                if ramp:
                    tl = ramp.find('top_left')
                    br = ramp.find('bottom_right')
                    if tl and br:
                        r1 = int(float(tl.find('red').text) * 255)
                        g1 = int(float(tl.find('green').text) * 255)
                        b1 = int(float(tl.find('blue').text) * 255)
                        r2 = int(float(br.find('bottom_right/red').text if br.find('bottom_right/red') else br.find('red').text) * 255)
                        g2 = int(float(br.find('bottom_right/green').text if br.find('bottom_right/green') else br.find('green').text) * 255)
                        b2 = int(float(br.find('bottom_right/blue').text if br.find('bottom_right/blue') else br.find('blue').text) * 255)
                        print(f"  上: RGB({r1}, {g1}, {b1})")
                        print(f"  下: RGB({r2}, {g2}, {b2})")

            elif fill_type == 5:  # 単色
                solid = colouring.find('solid_colour/all')
                if solid:
                    r = int(float(solid.find('red').text) * 255)
                    g = int(float(solid.find('green').text) * 255)
                    b = int(float(solid.find('blue').text) * 255)
                    print(f"  色: RGB({r}, {g}, {b})")

    # 2. シャドウ
    shadow = sd.find('shadow')
    if shadow:
        on = shadow.find('on')
        if on is not None and on.text == 'true':
            print(f"\n[シャドウ] 有効")

            softness = shadow.find('softness')
            if softness is not None:
                print(f"  ぼかし: {softness.text}")

            colour = shadow.find('colour')
            if colour:
                r = int(float(colour.find('red').text) * 255)
                g = int(float(colour.find('green').text) * 255)
                b = int(float(colour.find('blue').text) * 255)
                a = int(float(colour.find('alpha').text) * 255)
                print(f"  色: RGBA({r}, {g}, {b}, {a})")

            offset = shadow.find('offset')
            if offset:
                angle = offset.find('angle')
                magnitude = offset.find('magnitude')
                if angle is not None and magnitude is not None:
                    print(f"  角度: {angle.text}°")
                    print(f"  距離: {magnitude.text}")

    # 3. エンベリッシュメント
    inner_count_elem = sd.find('inner_embellishment_count')
    if inner_count_elem is not None:
        inner_count = int(inner_count_elem.text)
        if inner_count > 0:
            print(f"\n[エンベリッシュメント] 数: {inner_count}")

            for j in range(12):
                emb_name = f'embellishment__{j}' if j < 10 else f'embellishment_{j}'
                emb = sd.find(emb_name)

                if emb is not None:
                    existence = emb.find('existence')
                    if existence is not None and int(existence.text) == 1:
                        print(f"  #{j}: 有効")

print(f"\n{'='*80}")
print("解析完了")
print('='*80)
