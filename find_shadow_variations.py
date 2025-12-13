#!/usr/bin/env python3
"""
複数のFontstyleを解析してシャドウパラメータのバリエーションを探す
"""

import xml.etree.ElementTree as ET
import base64
import struct

def get_style_binary(filepath, style_name):
    """スタイルのバイナリデータを取得"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    for style_item in root.findall('.//StyleProjectItem'):
        name_elem = style_item.find('.//Name')
        if name_elem is not None and name_elem.text == style_name:
            component_ref_elem = style_item.find('.//Component[@ObjectRef]')
            component_ref = component_ref_elem.get('ObjectRef')
            vfc = root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")
            first_param_ref = vfc.find(".//Param[@Index='0']")
            param_obj_ref = first_param_ref.get('ObjectRef')
            arb_param = root.find(f".//ArbVideoComponentParam[@ObjectID='{param_obj_ref}']")
            binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
            return base64.b64decode(binary_elem.text.strip())
    return None

def list_styles(filepath):
    """ファイル内のスタイル一覧を取得"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    styles = []
    for style_item in root.findall('.//StyleProjectItem'):
        name_elem = style_item.find('.//Name')
        if name_elem is not None:
            styles.append(name_elem.text)

    return styles

def find_shadow_params(binary):
    """シャドウパラメータを検索"""
    results = {
        'size': len(binary),
        'xy_offsets': [],
        'blur_candidates': []
    }

    # X,Yオフセットペア
    for offset in range(0, len(binary) - 7, 4):
        try:
            x = struct.unpack('<f', binary[offset:offset+4])[0]
            y = struct.unpack('<f', binary[offset+4:offset+8])[0]

            if -50.0 <= x <= 50.0 and -50.0 <= y <= 50.0:
                if abs(x - round(x)) < 0.1 and abs(y - round(y)) < 0.1:
                    if abs(x) > 0.1 or abs(y) > 0.1:
                        # 近くのぼかし候補を探す
                        blur_before = None
                        blur_after = None

                        # -12バイト前から+16バイト後までを調べる
                        for delta in [-12, -8, -4, 0, 4, 8, 12, 16]:
                            blur_offset = offset + delta
                            if 0 <= blur_offset + 4 <= len(binary):
                                try:
                                    val = struct.unpack('<f', binary[blur_offset:blur_offset+4])[0]
                                    if 0 <= val <= 100 and abs(val - round(val)) < 0.1:
                                        if delta < 0:
                                            blur_before = (delta, val)
                                        elif delta > 0:
                                            if blur_after is None:
                                                blur_after = (delta, val)
                                except:
                                    pass

                        results['xy_offsets'].append({
                            'offset': offset,
                            'x': x,
                            'y': y,
                            'blur_before': blur_before,
                            'blur_after': blur_after
                        })
        except:
            pass

    # すべてのfloat値から典型的なぼかし値（5, 10, 20, 50, 100など）を探す
    for offset in range(0, len(binary) - 3, 4):
        try:
            val = struct.unpack('<f', binary[offset:offset+4])[0]
            # 5の倍数または典型的なぼかし値
            if val in [0, 1, 2, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100]:
                results['blur_candidates'].append((offset, val))
        except:
            pass

    return results

def main():
    filepath = "prtextstyle/100 New Fonstyle.prtextstyle"
    styles = list_styles(filepath)

    print("="*80)
    print(f"全{len(styles)}個のFontstyleを解析")
    print("="*80)
    print()

    shadow_styles = []

    for style_name in styles:
        binary = get_style_binary(filepath, style_name)
        if binary:
            params = find_shadow_params(binary)

            # X,Yオフセットが見つかったもののみ
            if len(params['xy_offsets']) > 0:
                shadow_styles.append({
                    'name': style_name,
                    'size': params['size'],
                    'shadow_count': len(params['xy_offsets']),
                    'params': params
                })

    print(f"シャドウパラメータが検出されたスタイル: {len(shadow_styles)} 個")
    print()

    # サイズでグループ化
    size_groups = {}
    for style in shadow_styles:
        size = style['size']
        if size not in size_groups:
            size_groups[size] = []
        size_groups[size].append(style)

    print(f"サイズバリエーション: {len(size_groups)} 種類")
    for size in sorted(size_groups.keys()):
        print(f"  {size:5d} bytes: {len(size_groups[size]):3d} スタイル")
    print()

    # 詳細表示（最初の20個）
    print("="*80)
    print("シャドウパラメータ詳細（最初の20個）")
    print("="*80)
    print()

    for i, style in enumerate(shadow_styles[:20], 1):
        print(f"{i:2d}. {style['name']} ({style['size']} bytes, {style['shadow_count']}個のシャドウ)")

        for j, xy in enumerate(style['params']['xy_offsets'][:5], 1):
            blur_info = ""
            if xy['blur_before']:
                delta, val = xy['blur_before']
                blur_info += f" Blur前{delta:+3d}={val:.0f}"
            if xy['blur_after']:
                delta, val = xy['blur_after']
                blur_info += f" Blur後{delta:+3d}={val:.0f}"

            print(f"   {j}. 0x{xy['offset']:04x}: X={xy['x']:5.1f}, Y={xy['y']:5.1f}{blur_info}")

        print()

    # ぼかし値の統計
    print("="*80)
    print("ぼかし値の統計")
    print("="*80)
    print()

    all_blur_values = {}
    for style in shadow_styles:
        for xy in style['params']['xy_offsets']:
            if xy['blur_before']:
                _, val = xy['blur_before']
                if val not in all_blur_values:
                    all_blur_values[val] = 0
                all_blur_values[val] += 1
            if xy['blur_after']:
                _, val = xy['blur_after']
                if val not in all_blur_values:
                    all_blur_values[val] = 0
                all_blur_values[val] += 1

    print("検出されたぼかし値の頻度:")
    for val in sorted(all_blur_values.keys()):
        count = all_blur_values[val]
        print(f"  Blur = {val:5.0f}: {count:3d} 回")

if __name__ == "__main__":
    main()
