#!/usr/bin/env python3
"""
エンベリッシュメント（装飾・境界線）の解析
"""

import xml.etree.ElementTree as ET

prsl_path = '/home/user/telop01/10styles/10styles.prsl'

tree = ET.parse(prsl_path)
root = tree.getroot()

print("="*80)
print("エンベリッシュメント解析")
print("="*80)

for i, styleblock in enumerate(root.findall('.//styleblock'), 1):
    name = styleblock.get('name', 'Unknown')

    style_data = styleblock.find('style_data')
    if not style_data:
        continue

    # エンベリッシュメント数を取得
    inner_count = style_data.find('inner_embellishment_count')
    count = int(inner_count.text) if inner_count is not None else 0

    if count > 0:
        print(f"\n{'='*80}")
        print(f"スタイル {i}: {name}")
        print('='*80)
        print(f"エンベリッシュメント数: {count}")

        # 各エンベリッシュメントを確認
        for j in range(12):  # embellishment__0 to embellishment_11
            emb = style_data.find(f'embellishment__{j}')
            if emb is None:
                emb = style_data.find(f'embellishment_{j:02d}')  # embellishment_10, embellishment_11

            if emb is not None:
                print(f"\n  エンベリッシュメント {j}:")

                # タイプ
                emb_type = emb.find('type')
                if emb_type is not None:
                    type_val = int(emb_type.text)
                    type_names = {
                        0: "なし",
                        1: "境界線（Stroke）",
                        2: "シャドウ（Shadow）",
                        3: "グロー（Glow）"
                    }
                    print(f"    タイプ: {type_val} = {type_names.get(type_val, '不明')}")

                # 幅
                width = emb.find('width')
                if width is not None:
                    print(f"    幅: {width.text}")

                # 色
                colouring = emb.find('shader/colouring')
                if colouring:
                    solid = colouring.find('solid_colour/all')
                    if solid:
                        r = float(solid.find('red').text)
                        g = float(solid.find('green').text)
                        b = float(solid.find('blue').text)
                        a = float(solid.find('alpha').text)
                        print(f"    色: RGBA({int(r*255)}, {int(g*255)}, {int(b*255)}, {int(a*255)})")

                # ぼかし
                softness = emb.find('softness')
                if softness is not None:
                    print(f"    ぼかし: {softness.text}")

print(f"\n{'='*80}")
