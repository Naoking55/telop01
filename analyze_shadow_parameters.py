#!/usr/bin/env python3
"""
シャドウパラメータの解析
Fontstyle_90 (1756バイト) を詳細解析してシャドウパラメータを特定
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

def find_float_sequences(binary, min_val=-100.0, max_val=100.0):
    """連続するfloat値のシーケンスを検索"""
    sequences = []

    for offset in range(0, len(binary) - 11, 4):
        try:
            vals = []
            for i in range(3):
                val = struct.unpack('<f', binary[offset+i*4:offset+i*4+4])[0]
                vals.append(val)

            # すべてが範囲内か？
            if all(min_val <= v <= max_val for v in vals):
                sequences.append((offset, vals))
        except:
            pass

    return sequences

def find_rgba_colors(binary):
    """RGBA float色を検索"""
    colors = []

    for offset in range(0, len(binary) - 15, 4):
        try:
            r = struct.unpack('<f', binary[offset:offset+4])[0]
            g = struct.unpack('<f', binary[offset+4:offset+8])[0]
            b = struct.unpack('<f', binary[offset+8:offset+12])[0]
            a = struct.unpack('<f', binary[offset+12:offset+16])[0]

            if all(-0.1 <= v <= 1.1 for v in [r, g, b, a]):
                # 特徴的な色
                color_name = ''
                if abs(r) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1:
                    color_name = '黒'
                elif abs(b - 1.0) < 0.1 and abs(r) < 0.1 and abs(g) < 0.1:
                    color_name = '青'
                elif abs(r - 1.0) < 0.1 and abs(g - 1.0) < 0.1 and abs(b - 1.0) < 0.1:
                    color_name = '白'

                if color_name:
                    colors.append((offset, r, g, b, a, color_name))
        except:
            pass

    return colors

def find_small_float_values(binary, max_val=50.0):
    """小さなfloat値を検索（シャドウのオフセット候補）"""
    values = []

    for offset in range(0, len(binary) - 3, 4):
        try:
            val = struct.unpack('<f', binary[offset:offset+4])[0]
            if -max_val <= val <= max_val and abs(val) > 0.01:
                values.append((offset, val))
        except:
            pass

    return values

def main():
    filepath = "prtextstyle/100 New Fonstyle.prtextstyle"

    # Fontstyle_01 (シンプル) と Fontstyle_90 (複雑) を比較
    bin_01 = get_style_binary(filepath, "Fontstyle_01")
    bin_90 = get_style_binary(filepath, "Fontstyle_90")

    if not bin_01 or not bin_90:
        print("❌ スタイルの取得に失敗")
        return

    print("="*80)
    print("シャドウパラメータの解析")
    print("="*80)
    print()

    print(f"Fontstyle_01 (シンプル): {len(bin_01)} bytes")
    print(f"Fontstyle_90 (複雑):     {len(bin_90)} bytes")
    print(f"差分:                     {len(bin_90) - len(bin_01)} bytes (+{(len(bin_90) - len(bin_01)) / (len(bin_90) - len(bin_01)) * 100:.0f}%)")
    print()

    # RGBA色を検出
    print("="*80)
    print("RGBA Float色の検出")
    print("="*80)
    print()

    colors_01 = find_rgba_colors(bin_01)
    colors_90 = find_rgba_colors(bin_90)

    print(f"Fontstyle_01: {len(colors_01)} 箇所")
    for offset, r, g, b, a, color_name in colors_01:
        r255 = int(r * 255)
        g255 = int(g * 255)
        b255 = int(b * 255)
        a255 = int(a * 255)
        print(f"  0x{offset:04x}: {color_name:4s} RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f}) = RGB({r255:3d}, {g255:3d}, {b255:3d}, {a255:3d})")

    print()
    print(f"Fontstyle_90: {len(colors_90)} 箇所")
    for offset, r, g, b, a, color_name in colors_90:
        r255 = int(r * 255)
        g255 = int(g * 255)
        b255 = int(b * 255)
        a255 = int(a * 255)
        print(f"  0x{offset:04x}: {color_name:4s} RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f}) = RGB({r255:3d}, {g255:3d}, {b255:3d}, {a255:3d})")

    # 小さなfloat値（シャドウオフセット候補）
    print()
    print("="*80)
    print("小さなfloat値の検索（シャドウオフセット候補）")
    print("="*80)
    print()

    small_vals_90 = find_small_float_values(bin_90, max_val=20.0)

    print(f"Fontstyle_90で検出された小さなfloat値: {len(small_vals_90)} 箇所")
    print()

    # 典型的なシャドウオフセット値（1.0-10.0の範囲）をハイライト
    shadow_candidates = [(offset, val) for offset, val in small_vals_90
                         if 0.5 <= abs(val) <= 15.0]

    print(f"シャドウオフセット候補（0.5-15.0の範囲）: {len(shadow_candidates)} 箇所")
    print()

    # 値でグループ化
    value_groups = {}
    for offset, val in shadow_candidates:
        val_key = f"{val:.2f}"
        if val_key not in value_groups:
            value_groups[val_key] = []
        value_groups[val_key].append(offset)

    for val_key in sorted(value_groups.keys(), key=lambda x: abs(float(x))):
        offsets = value_groups[val_key]
        print(f"  値 {float(val_key):6.2f}: {len(offsets):2d} 箇所")
        for offset in offsets[:5]:  # 最初の5箇所のみ
            print(f"    0x{offset:04x}")

    # 連続するfloat値のペア（X, Y オフセット候補）
    print()
    print("="*80)
    print("連続する2つのfloat値（シャドウ X, Y オフセット候補）")
    print("="*80)
    print()

    xy_candidates = []
    for offset in range(0, len(bin_90) - 7, 4):
        try:
            x = struct.unpack('<f', bin_90[offset:offset+4])[0]
            y = struct.unpack('<f', bin_90[offset+4:offset+8])[0]

            # 両方が小さな値（-20 ~ 20）の範囲
            if -20.0 <= x <= 20.0 and -20.0 <= y <= 20.0 and (abs(x) > 0.1 or abs(y) > 0.1):
                # 整数に近い値を優先
                if abs(x - round(x)) < 0.1 and abs(y - round(y)) < 0.1:
                    xy_candidates.append((offset, x, y))
        except:
            pass

    print(f"検出されたX, Yペア候補: {len(xy_candidates)} 箇所")
    print()

    for i, (offset, x, y) in enumerate(xy_candidates[:20], 1):
        print(f"{i:2d}. 0x{offset:04x}: X={x:6.2f}, Y={y:6.2f}")

        # 周辺に色があるか確認
        nearby_colors = []
        for color_offset, r, g, b, a, color_name in colors_90:
            distance = color_offset - offset
            if -40 <= distance <= 40:
                nearby_colors.append((distance, color_offset, color_name))

        if nearby_colors:
            print(f"      近くの色: ", end="")
            for distance, color_offset, color_name in sorted(nearby_colors, key=lambda x: abs(x[0]))[:3]:
                print(f"{color_name}@0x{color_offset:04x}({distance:+3d}) ", end="")
            print()

    # 特定のパターン: 黒色 + オフセットペア
    print()
    print("="*80)
    print("黒色の近くのX, Yオフセットペア")
    print("="*80)
    print()

    black_colors = [c for c in colors_90 if c[5] == '黒']
    print(f"検出された黒色: {len(black_colors)} 箇所")
    print()

    for offset, r, g, b, a, color_name in black_colors:
        print(f"黒色 @ 0x{offset:04x}: RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f})")

        # 前後40バイトでX,Yペアを探す
        nearby_xy = []
        for xy_offset, x, y in xy_candidates:
            distance = xy_offset - offset
            if -40 <= distance <= 40:
                nearby_xy.append((distance, xy_offset, x, y))

        if nearby_xy:
            for distance, xy_offset, x, y in sorted(nearby_xy, key=lambda x: abs(x[0]))[:3]:
                print(f"  X,Y @ 0x{xy_offset:04x} (距離: {distance:+3d}): X={x:6.2f}, Y={y:6.2f}")

        print()

if __name__ == "__main__":
    main()
