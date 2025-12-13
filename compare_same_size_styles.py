#!/usr/bin/env python3
"""
同じサイズのスタイル同士を比較
シャドウパラメータだけが異なるペアを見つける
"""

import xml.etree.ElementTree as ET
import base64
import struct

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

def count_differences(bin1, bin2):
    """2つのバイナリの差分バイト数をカウント"""
    if len(bin1) != len(bin2):
        return None

    diff_count = 0
    for i in range(len(bin1)):
        if bin1[i] != bin2[i]:
            diff_count += 1

    return diff_count

def find_difference_regions(bin1, bin2):
    """差分領域を検出"""
    if len(bin1) != len(bin2):
        return []

    differences = []
    i = 0
    while i < len(bin1):
        if bin1[i] != bin2[i]:
            start = i
            while i < len(bin1) and bin1[i] != bin2[i]:
                i += 1
            end = i
            differences.append((start, end))
        else:
            i += 1

    return differences

def analyze_float_difference(bin1, bin2, offset):
    """オフセット位置のfloat値の差分を解析"""
    try:
        val1 = struct.unpack('<f', bin1[offset:offset+4])[0]
        val2 = struct.unpack('<f', bin2[offset:offset+4])[0]
        return val1, val2
    except:
        return None, None

def main():
    filepath = "prtextstyle/100 New Fonstyle.prtextstyle"
    styles = get_all_styles_from_file(filepath)

    print("="*80)
    print("同じサイズのスタイル比較")
    print("="*80)
    print()

    # サイズでグループ化
    size_groups = {}
    for name, binary in styles.items():
        size = len(binary)
        if size not in size_groups:
            size_groups[size] = []
        size_groups[size].append((name, binary))

    # 732 bytesのグループを詳細比較
    target_size = 732
    if target_size in size_groups:
        group = size_groups[target_size]
        print(f"{target_size} bytesのスタイル: {len(group)} 個")
        print()

        # 最初の2つを比較
        if len(group) >= 2:
            name1, bin1 = group[0]
            name2, bin2 = group[1]

            print(f"比較: {name1} vs {name2}")
            print()

            diff_count = count_differences(bin1, bin2)
            print(f"差分バイト数: {diff_count} / {len(bin1)} bytes ({diff_count / len(bin1) * 100:.1f}%)")
            print()

            differences = find_difference_regions(bin1, bin2)
            print(f"差分領域: {len(differences)} 箇所")
            print()

            # 差分領域を表示
            for i, (start, end) in enumerate(differences, 1):
                size = end - start
                print(f"{i:2d}. 0x{start:04x} - 0x{end:04x} ({size:3d} bytes)")

                # Float値として解析（最初の8個）
                float_diffs = []
                for offset in range(start, min(start + 32, end), 4):
                    val1, val2 = analyze_float_difference(bin1, bin2, offset)
                    if val1 is not None and val2 is not None:
                        if abs(val1) < 10000 and abs(val2) < 10000:
                            if abs(val1 - val2) > 0.01:
                                float_diffs.append((offset, val1, val2))

                if float_diffs:
                    for offset, val1, val2 in float_diffs[:8]:
                        print(f"    0x{offset:04x}: {val1:10.4f} → {val2:10.4f}")

                print()

        # 全ペアで最小差分を探す
        print("="*80)
        print("最小差分のスタイルペアを探索")
        print("="*80)
        print()

        min_diff = float('inf')
        min_pair = None

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                name1, bin1 = group[i]
                name2, bin2 = group[j]

                diff_count = count_differences(bin1, bin2)
                if diff_count is not None and diff_count < min_diff:
                    min_diff = diff_count
                    min_pair = (name1, name2, bin1, bin2)

        if min_pair:
            name1, name2, bin1, bin2 = min_pair
            print(f"最小差分ペア: {name1} vs {name2}")
            print(f"差分バイト数: {min_diff} / {len(bin1)} bytes ({min_diff / len(bin1) * 100:.1f}%)")
            print()

            differences = find_difference_regions(bin1, bin2)
            print(f"差分領域: {len(differences)} 箇所")
            print()

            # 差分領域を詳細表示
            for i, (start, end) in enumerate(differences[:20], 1):
                size = end - start
                print(f"{i:2d}. 0x{start:04x} - 0x{end:04x} ({size:3d} bytes)")

                # Hex dump
                print(f"    {name1}: ", end="")
                print(' '.join(f'{b:02x}' for b in bin1[start:min(start+16, end)]))
                print(f"    {name2}: ", end="")
                print(' '.join(f'{b:02x}' for b in bin2[start:min(start+16, end)]))

                # Float値として解析
                float_diffs = []
                for offset in range(start, min(start + 32, end), 4):
                    val1, val2 = analyze_float_difference(bin1, bin2, offset)
                    if val1 is not None and val2 is not None:
                        if abs(val1) < 10000 and abs(val2) < 10000:
                            if abs(val1 - val2) > 0.01:
                                float_diffs.append((offset, val1, val2))

                if float_diffs:
                    print("    Float値:")
                    for offset, val1, val2 in float_diffs[:5]:
                        print(f"      0x{offset:04x}: {val1:10.4f} → {val2:10.4f}")

                print()

if __name__ == "__main__":
    main()
