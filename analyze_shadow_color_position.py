#!/usr/bin/env python3
"""
シャドウなし/ありスタイルの完全比較
シャドウ色とシャドウ有無フラグを特定
"""

import xml.etree.ElementTree as ET
import base64
import struct
import sys

def get_all_styles_from_file(filepath):
    """ファイルから全スタイルのバイナリを取得"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    styles = {}
    for style_item in root.findall('.//StyleProjectItem'):
        name_elem = style_item.find('.//Name')
        if name_elem is not None:
            style_name = name_elem.text
            component_ref_elem = style_item.find('.//Component[@ObjectRef]')
            component_ref = component_ref_elem.get('ObjectRef')
            vfc = root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")
            first_param_ref = vfc.find(".//Param[@Index='0']")
            param_obj_ref = first_param_ref.get('ObjectRef')
            arb_param = root.find(f".//ArbVideoComponentParam[@ObjectID='{param_obj_ref}']")
            binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
            binary = base64.b64decode(binary_elem.text.strip())
            styles[style_name] = binary

    return styles

def find_rgba_colors(binary):
    """RGBA float色を検索（Alpha > 0のみ）"""
    colors = []

    for offset in range(0, len(binary) - 15, 4):
        try:
            r = struct.unpack('<f', binary[offset:offset+4])[0]
            g = struct.unpack('<f', binary[offset+4:offset+8])[0]
            b = struct.unpack('<f', binary[offset+8:offset+12])[0]
            a = struct.unpack('<f', binary[offset+12:offset+16])[0]

            if all(0.0 <= v <= 1.0 for v in [r, g, b, a]) and a > 0.01:
                color_name = ''
                if abs(r) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1:
                    color_name = '黒'
                elif abs(b - 1.0) < 0.1 and abs(r) < 0.1 and abs(g) < 0.1:
                    color_name = '青'
                elif abs(r - 1.0) < 0.1 and abs(g - 1.0) < 0.1 and abs(b - 1.0) < 0.1:
                    color_name = '白'
                elif abs(r - 1.0) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1:
                    color_name = '赤'

                if color_name:
                    colors.append({
                        'offset': offset,
                        'r': r, 'g': g, 'b': b, 'a': a,
                        'name': color_name
                    })
        except:
            pass

    return colors

def find_xy_offsets(binary):
    """X,Yオフセットペアを検索"""
    xy_pairs = []

    for offset in range(0, len(binary) - 7, 4):
        try:
            x = struct.unpack('<f', binary[offset:offset+4])[0]
            y = struct.unpack('<f', binary[offset+4:offset+8])[0]

            if -50.0 <= x <= 50.0 and -50.0 <= y <= 50.0:
                if abs(x - round(x)) < 0.1 and abs(y - round(y)) < 0.1:
                    if abs(x) > 0.5 or abs(y) > 0.5:  # (0,0)に近いものは除外
                        xy_pairs.append({
                            'offset': offset,
                            'x': x,
                            'y': y
                        })
        except:
            pass

    return xy_pairs

def find_byte_differences(bin1, bin2):
    """バイト単位の差分を検出"""
    min_len = min(len(bin1), len(bin2))
    differences = []

    i = 0
    while i < min_len:
        if bin1[i] != bin2[i]:
            start = i
            while i < min_len and bin1[i] != bin2[i]:
                i += 1
            end = i
            differences.append((start, end))
        else:
            i += 1

    if len(bin1) != len(bin2):
        differences.append((min_len, max(len(bin1), len(bin2))))

    return differences

def analyze_difference_region(bin1, bin2, start, end):
    """差分領域をfloat値として解析"""
    results = []

    for offset in range(start, min(end, len(bin1) - 3, len(bin2) - 3), 4):
        try:
            val1 = struct.unpack('<f', bin1[offset:offset+4])[0] if offset + 4 <= len(bin1) else None
            val2 = struct.unpack('<f', bin2[offset:offset+4])[0] if offset + 4 <= len(bin2) else None

            if val1 is not None and val2 is not None:
                if abs(val1) < 10000 and abs(val2) < 10000:  # 妥当な範囲
                    results.append((offset, val1, val2))
        except:
            pass

    return results

def dump_hex_comparison(bin1, bin2, start, end):
    """2つのバイナリの16進ダンプ比較"""
    print(f"\n16進ダンプ比較 (0x{start:04x} - 0x{end:04x}):")
    print(f"{'Offset':<10} {'Binary1':<50} {'Binary2':<50}")
    print("-" * 110)

    for offset in range(start, end, 16):
        hex1 = ' '.join(f'{b:02x}' for b in bin1[offset:min(offset+16, end, len(bin1))])
        hex2 = ' '.join(f'{b:02x}' for b in bin2[offset:min(offset+16, end, len(bin2))])
        print(f"0x{offset:04x}:   {hex1:<48} | {hex2:<48}")

def main():
    filepath = "prtextstyle/100 New Fonstyle.prtextstyle"

    # 全スタイルを取得
    styles = get_all_styles_from_file(filepath)

    print("="*80)
    print("シャドウなし/ありスタイルの比較解析")
    print("="*80)
    print()

    # サイズでグループ化
    size_groups = {}
    for name, binary in styles.items():
        size = len(binary)
        if size not in size_groups:
            size_groups[size] = []
        size_groups[size].append(name)

    print("スタイルのサイズグループ:")
    for size in sorted(size_groups.keys())[:10]:
        count = len(size_groups[size])
        print(f"  {size:5d} bytes: {count:3d} スタイル - {', '.join(size_groups[size][:3])}")
    print()

    # 最も小さいサイズのグループを選択（シンプルなスタイル）
    smallest_size = min(size_groups.keys())
    simple_styles = size_groups[smallest_size]

    print(f"最もシンプルなスタイル ({smallest_size} bytes): {len(simple_styles)} 個")
    print(f"  {', '.join(simple_styles[:10])}")
    print()

    # Fontstyle_01 vs Fontstyle_90を詳細比較
    style1_name = "Fontstyle_01"
    style2_name = "Fontstyle_90"

    if style1_name not in styles or style2_name not in styles:
        print(f"❌ {style1_name} または {style2_name} が見つかりません")
        return

    bin1 = styles[style1_name]
    bin2 = styles[style2_name]

    print("="*80)
    print(f"詳細比較: {style1_name} ({len(bin1)} bytes) vs {style2_name} ({len(bin2)} bytes)")
    print("="*80)
    print()

    # RGBA色を検出
    colors1 = find_rgba_colors(bin1)
    colors2 = find_rgba_colors(bin2)

    print(f"【{style1_name}】RGBA色（Alpha > 0）: {len(colors1)} 箇所")
    for c in colors1:
        print(f"  0x{c['offset']:04x}: {c['name']:4s} RGBA({c['r']:.2f}, {c['g']:.2f}, {c['b']:.2f}, {c['a']:.2f})")

    print()
    print(f"【{style2_name}】RGBA色（Alpha > 0）: {len(colors2)} 箇所")
    for c in colors2:
        print(f"  0x{c['offset']:04x}: {c['name']:4s} RGBA({c['r']:.2f}, {c['g']:.2f}, {c['b']:.2f}, {c['a']:.2f})")

    print()

    # 追加された黒色RGBAを検出
    offsets1_black = set(c['offset'] for c in colors1 if c['name'] == '黒')
    new_black = [c for c in colors2 if c['name'] == '黒' and c['offset'] not in offsets1_black]

    print("="*80)
    print(f"追加された黒色RGBA（{style2_name}のみ）: {len(new_black)} 箇所")
    print("="*80)
    print()

    if new_black:
        for c in new_black:
            print(f"  0x{c['offset']:04x}: RGBA({c['r']:.2f}, {c['g']:.2f}, {c['b']:.2f}, {c['a']:.2f})")
    else:
        print("  (追加された黒色なし)")

    print()

    # X,Yオフセットペアを検出
    xy1 = find_xy_offsets(bin1)
    xy2 = find_xy_offsets(bin2)

    offsets1_xy = set(x['offset'] for x in xy1)
    new_xy = [x for x in xy2 if x['offset'] not in offsets1_xy]

    print("="*80)
    print(f"追加されたX,Yオフセットペア（{style2_name}のみ）: {len(new_xy)} 箇所")
    print("="*80)
    print()

    for xy in new_xy[:10]:
        print(f"\n📍 X,Yオフセット @ 0x{xy['offset']:04x}: X={xy['x']:.1f}, Y={xy['y']:.1f}")

        # 前後の黒色RGBAを探す
        nearby_black = []
        for c in new_black:
            distance = c['offset'] - xy['offset']
            if -64 <= distance <= 64:
                nearby_black.append((distance, c))

        if nearby_black:
            print("  近くの黒色RGBA:")
            for distance, c in sorted(nearby_black, key=lambda x: abs(x[0]))[:5]:
                print(f"    距離 {distance:+4d} @ 0x{c['offset']:04x}: RGBA({c['r']:.2f}, {c['g']:.2f}, {c['b']:.2f}, {c['a']:.2f})")

        # Blur候補を探す
        for delta in [-12, -8, -4, 4, 8, 12, 16]:
            blur_offset = xy['offset'] + delta
            if 0 <= blur_offset + 4 <= len(bin2):
                try:
                    val = struct.unpack('<f', bin2[blur_offset:blur_offset+4])[0]
                    if 0 <= val <= 100:
                        print(f"  Blur候補 @ 0x{blur_offset:04x} (距離{delta:+3d}): {val:.1f}")
                except:
                    pass

    # バイト差分解析
    print()
    print("="*80)
    print("バイト単位の差分領域")
    print("="*80)
    print()

    differences = find_byte_differences(bin1, bin2)
    print(f"差分領域: {len(differences)} 箇所")
    print()

    # 大きな差分領域のみ表示（16バイト以上）
    large_diffs = [(start, end) for start, end in differences if end - start >= 16]
    print(f"大きな差分領域（16バイト以上）: {len(large_diffs)} 箇所")
    print()

    for i, (start, end) in enumerate(large_diffs[:5], 1):
        print(f"\n{i}. 差分領域 0x{start:04x} - 0x{end:04x} ({end - start} bytes)")

        # この領域に黒色RGBAやX,Yオフセットがあるか
        in_region_black = [c for c in new_black if start <= c['offset'] < end]
        in_region_xy = [x for x in new_xy if start <= x['offset'] < end]

        if in_region_black:
            print(f"  この領域内の黒色RGBA: {len(in_region_black)} 箇所")
            for c in in_region_black:
                print(f"    0x{c['offset']:04x}: RGBA({c['r']:.2f}, {c['g']:.2f}, {c['b']:.2f}, {c['a']:.2f})")

        if in_region_xy:
            print(f"  この領域内のX,Yオフセット: {len(in_region_xy)} 箇所")
            for xy in in_region_xy:
                print(f"    0x{xy['offset']:04x}: X={xy['x']:.1f}, Y={xy['y']:.1f}")

        # float値として解析
        float_vals = analyze_difference_region(bin1, bin2, start, min(start + 64, end))
        if float_vals:
            print(f"  Float値の変化（最初の10個）:")
            for offset, val1, val2 in float_vals[:10]:
                if abs(val1 - val2) > 0.01:
                    print(f"    0x{offset:04x}: {val1:10.4f} → {val2:10.4f}")

if __name__ == "__main__":
    main()
