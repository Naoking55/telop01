#!/usr/bin/env python3
"""
シャドウあり/なしの比較解析
シンプルな白色スタイルのシャドウパラメータを特定
"""

import xml.etree.ElementTree as ET
import base64
import struct
import sys

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

def find_differences(bin1, bin2):
    """2つのバイナリデータの差分を検出"""
    if not bin1 or not bin2:
        return []

    min_len = min(len(bin1), len(bin2))
    differences = []

    i = 0
    while i < min_len:
        if bin1[i] != bin2[i]:
            # 差分の開始位置を記録
            start = i
            # 連続する差分をまとめる
            while i < min_len and bin1[i] != bin2[i]:
                i += 1
            end = i
            differences.append((start, end))
        else:
            i += 1

    # サイズの違いも記録
    if len(bin1) != len(bin2):
        differences.append((min_len, max(len(bin1), len(bin2))))

    return differences

def analyze_float_at_offset(binary, offset, context=4):
    """オフセット位置のfloat値を解析"""
    if offset + 3 >= len(binary):
        return None

    try:
        val = struct.unpack('<f', binary[offset:offset+4])[0]
        return val
    except:
        return None

def find_shadow_candidates(binary):
    """シャドウパラメータ候補を検索"""
    candidates = {
        'xy_offsets': [],
        'blur_values': [],
        'rgba_colors': []
    }

    # X,Yオフセットペア（-50 ~ 50の範囲）
    for offset in range(0, len(binary) - 7, 4):
        try:
            x = struct.unpack('<f', binary[offset:offset+4])[0]
            y = struct.unpack('<f', binary[offset+4:offset+8])[0]

            if -50.0 <= x <= 50.0 and -50.0 <= y <= 50.0:
                # 整数に近い値を優先
                if abs(x - round(x)) < 0.1 and abs(y - round(y)) < 0.1:
                    if abs(x) > 0.1 or abs(y) > 0.1:  # (0,0)は除外
                        candidates['xy_offsets'].append((offset, x, y))
        except:
            pass

    # ぼかし値候補（0 ~ 100の範囲）
    for offset in range(0, len(binary) - 3, 4):
        try:
            val = struct.unpack('<f', binary[offset:offset+4])[0]
            if 0.0 <= val <= 100.0:
                # 整数または0.5刻みの値
                if abs(val - round(val * 2) / 2) < 0.1:
                    candidates['blur_values'].append((offset, val))
        except:
            pass

    # RGBA色（黒色のみ、Alpha > 0）
    for offset in range(0, len(binary) - 15, 4):
        try:
            r = struct.unpack('<f', binary[offset:offset+4])[0]
            g = struct.unpack('<f', binary[offset+4:offset+8])[0]
            b = struct.unpack('<f', binary[offset+8:offset+12])[0]
            a = struct.unpack('<f', binary[offset+12:offset+16])[0]

            # 黒色でAlpha > 0
            if abs(r) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1 and a > 0.1:
                candidates['rgba_colors'].append((offset, r, g, b, a))
        except:
            pass

    return candidates

def main():
    if len(sys.argv) < 2:
        print("使用方法: python3 analyze_shadow_comparison.py <prtextstyle_file> [style1] [style2]")
        print("\nファイルを指定するとスタイル一覧を表示します")
        print("style1とstyle2を指定すると、2つのスタイルを比較します")
        sys.exit(1)

    filepath = sys.argv[1]

    if len(sys.argv) == 2:
        # スタイル一覧を表示
        styles = list_styles(filepath)
        print(f"\n{filepath} に含まれるスタイル ({len(styles)}個):")
        print("=" * 80)
        for i, style in enumerate(styles, 1):
            print(f"{i:3d}. {style}")
        print()
        return

    style1_name = sys.argv[2]
    style2_name = sys.argv[3] if len(sys.argv) > 3 else None

    if not style2_name:
        # 1つのスタイルのシャドウ候補を解析
        bin1 = get_style_binary(filepath, style1_name)
        if not bin1:
            print(f"❌ スタイル '{style1_name}' が見つかりません")
            return

        print("=" * 80)
        print(f"シャドウパラメータ候補の検索: {style1_name}")
        print("=" * 80)
        print(f"サイズ: {len(bin1)} bytes")
        print()

        candidates = find_shadow_candidates(bin1)

        print(f"🔍 X,Yオフセットペア候補: {len(candidates['xy_offsets'])} 箇所")
        for offset, x, y in candidates['xy_offsets'][:20]:
            print(f"  0x{offset:04x}: X={x:6.2f}, Y={y:6.2f}")

        print()
        print(f"🔍 ぼかし値候補: {len(candidates['blur_values'])} 箇所")
        blur_values = {}
        for offset, val in candidates['blur_values']:
            val_key = f"{val:.1f}"
            if val_key not in blur_values:
                blur_values[val_key] = []
            blur_values[val_key].append(offset)

        for val_key in sorted(blur_values.keys(), key=lambda x: float(x)):
            offsets = blur_values[val_key]
            if len(offsets) <= 10:  # 頻出しすぎる値は除外
                print(f"  値 {float(val_key):6.1f}: {len(offsets):2d} 箇所", end="")
                if len(offsets) <= 3:
                    print(" - ", end="")
                    for offset in offsets:
                        print(f"0x{offset:04x} ", end="")
                print()

        print()
        print(f"🔍 黒色RGBA候補（シャドウ色）: {len(candidates['rgba_colors'])} 箇所")
        for offset, r, g, b, a in candidates['rgba_colors'][:10]:
            print(f"  0x{offset:04x}: RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f})")

    else:
        # 2つのスタイルを比較
        bin1 = get_style_binary(filepath, style1_name)
        bin2 = get_style_binary(filepath, style2_name)

        if not bin1 or not bin2:
            print("❌ スタイルの取得に失敗")
            return

        print("=" * 80)
        print(f"シャドウパラメータの比較解析")
        print("=" * 80)
        print(f"スタイル1: {style1_name} ({len(bin1)} bytes)")
        print(f"スタイル2: {style2_name} ({len(bin2)} bytes)")
        print(f"差分:      {abs(len(bin2) - len(bin1))} bytes")
        print()

        # 差分を検出
        differences = find_differences(bin1, bin2)
        print(f"🔍 差分領域: {len(differences)} 箇所")
        print()

        for i, (start, end) in enumerate(differences[:20], 1):
            print(f"{i:2d}. 0x{start:04x} - 0x{end:04x} ({end - start} bytes)")

            # float値として解釈
            for offset in range(start, min(start + 32, end), 4):
                if offset + 4 <= len(bin1) and offset + 4 <= len(bin2):
                    val1 = analyze_float_at_offset(bin1, offset)
                    val2 = analyze_float_at_offset(bin2, offset)

                    if val1 is not None and val2 is not None:
                        if abs(val1) < 1000 and abs(val2) < 1000:  # 妥当な範囲
                            print(f"    0x{offset:04x}: {val1:10.4f} → {val2:10.4f}")
            print()

        # 各スタイルのシャドウ候補を比較
        print("=" * 80)
        print("各スタイルのシャドウ候補")
        print("=" * 80)
        print()

        cand1 = find_shadow_candidates(bin1)
        cand2 = find_shadow_candidates(bin2)

        print(f"【{style1_name}】")
        print(f"  X,Yオフセットペア: {len(cand1['xy_offsets'])} 箇所")
        print(f"  黒色RGBA: {len(cand1['rgba_colors'])} 箇所")
        print()

        print(f"【{style2_name}】")
        print(f"  X,Yオフセットペア: {len(cand2['xy_offsets'])} 箇所")
        print(f"  黒色RGBA: {len(cand2['rgba_colors'])} 箇所")
        print()

        # 差分を表示
        print("=" * 80)
        print("追加されたX,Yオフセットペア（style2のみ）")
        print("=" * 80)
        print()

        offsets1 = set(o for o, x, y in cand1['xy_offsets'])
        new_xy = [(o, x, y) for o, x, y in cand2['xy_offsets'] if o not in offsets1]

        if new_xy:
            for offset, x, y in new_xy[:10]:
                print(f"  0x{offset:04x}: X={x:6.2f}, Y={y:6.2f}")
        else:
            print("  (なし)")
        print()

        print("=" * 80)
        print("追加された黒色RGBA（style2のみ）")
        print("=" * 80)
        print()

        offsets1_rgba = set(o for o, r, g, b, a in cand1['rgba_colors'])
        new_rgba = [(o, r, g, b, a) for o, r, g, b, a in cand2['rgba_colors'] if o not in offsets1_rgba]

        if new_rgba:
            for offset, r, g, b, a in new_rgba[:10]:
                print(f"  0x{offset:04x}: RGBA({r:.2f}, {g:.2f}, {b:.2f}, {a:.2f})")
        else:
            print("  (なし)")

if __name__ == "__main__":
    main()
