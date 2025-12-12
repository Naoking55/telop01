#!/usr/bin/env python3
"""
スタイルをパターン別に分類して比較
"""

import xml.etree.ElementTree as ET
import base64
import struct
from collections import defaultdict

def get_all_styles_with_binary(filepath):
    """全スタイルのバイナリデータを取得"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    styles = []
    style_items = root.findall('.//StyleProjectItem')

    for style_item in style_items:
        name_elem = style_item.find('.//Name')
        style_name = name_elem.text if name_elem is not None else "Unknown"

        component_ref_elem = style_item.find('.//Component[@ObjectRef]')
        if component_ref_elem is None:
            continue

        component_ref = component_ref_elem.get('ObjectRef')
        vfc = root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")
        if vfc is None:
            continue

        first_param_ref = vfc.find(".//Param[@Index='0']")
        if first_param_ref is None:
            continue

        param_obj_ref = first_param_ref.get('ObjectRef')
        arb_param = root.find(f".//ArbVideoComponentParam[@ObjectID='{param_obj_ref}']")
        if arb_param is None:
            continue

        binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
        if binary_elem is None or not binary_elem.text:
            continue

        try:
            binary_data = base64.b64decode(binary_elem.text.strip())
            styles.append({
                'name': style_name,
                'binary': binary_data,
                'size': len(binary_data)
            })
        except:
            pass

    return styles

def compare_two_binaries(bin1, bin2, name1, name2):
    """2つのバイナリを比較"""
    print(f"\n{'='*80}")
    print(f"比較: {name1} vs {name2}")
    print(f"サイズ: {len(bin1)} bytes vs {len(bin2)} bytes (差分: {abs(len(bin1) - len(bin2))} bytes)")
    print(f"{'='*80}\n")

    # 差分箇所を検出
    min_len = min(len(bin1), len(bin2))
    differences = []

    for i in range(min_len):
        if bin1[i] != bin2[i]:
            differences.append(i)

    print(f"差分バイト数: {len(differences)} / {min_len} ({len(differences)*100//min_len}%)")

    # 差分の多い領域を表示
    if differences:
        # 差分を連続した範囲にグループ化
        ranges = []
        start = differences[0]
        end = differences[0]

        for diff in differences[1:]:
            if diff == end + 1:
                end = diff
            else:
                ranges.append((start, end))
                start = diff
                end = diff
        ranges.append((start, end))

        print(f"\n差分領域 (最初の10個):")
        for start, end in ranges[:10]:
            length = end - start + 1
            print(f"  0x{start:04x} - 0x{end:04x} ({length} bytes)")

            # その領域のデータを表示
            print(f"    {name1}: {bin1[start:min(start+16, end+1)].hex()}")
            print(f"    {name2}: {bin2[start:min(start+16, end+1)].hex()}")

    # サイズ差がある場合
    if len(bin1) != len(bin2):
        print(f"\nサイズ差:")
        if len(bin1) > len(bin2):
            extra_start = len(bin2)
            extra_data = bin1[extra_start:]
            print(f"  {name1} の追加データ (0x{extra_start:04x}から{len(extra_data)}bytes):")
            print(f"    {extra_data[:32].hex()}...")
        else:
            extra_start = len(bin1)
            extra_data = bin2[extra_start:]
            print(f"  {name2} の追加データ (0x{extra_start:04x}から{len(extra_data)}bytes):")
            print(f"    {extra_data[:32].hex()}...")

def main():
    print("='*80}")
    print("スタイルパターン比較分析")
    print("='*80}")

    # 100 Fonstyleファイルから取得
    styles_100 = get_all_styles_with_binary("prtextstyle/100 New Fonstyle.prtextstyle")
    print(f"\n100 Fonstyle: {len(styles_100)} スタイル取得")

    # サイズでソート
    styles_100.sort(key=lambda x: x['size'])

    # サイズ分布を表示
    print(f"\nサイズ範囲: {styles_100[0]['size']} - {styles_100[-1]['size']} bytes")
    print(f"\nサイズ別サンプル:")
    print(f"  最小: {styles_100[0]['name']} ({styles_100[0]['size']} bytes)")
    print(f"  中央: {styles_100[len(styles_100)//2]['name']} ({styles_100[len(styles_100)//2]['size']} bytes)")
    print(f"  最大: {styles_100[-1]['name']} ({styles_100[-1]['size']} bytes)")

    # 最小と最大を比較
    compare_two_binaries(
        styles_100[0]['binary'],
        styles_100[-1]['binary'],
        styles_100[0]['name'],
        styles_100[-1]['name']
    )

    # 似たサイズのものを比較（連続した2つ）
    print(f"\n\n{'='*80}")
    print("類似サイズの比較（Fontstyle_01 vs Fontstyle_02）")
    print(f"{'='*80}")

    # Fontstyle_01とFontstyle_02を探す
    style_01 = next((s for s in styles_100 if s['name'] == 'Fontstyle_01'), None)
    style_02 = next((s for s in styles_100 if s['name'] == 'Fontstyle_02'), None)

    if style_01 and style_02:
        compare_two_binaries(
            style_01['binary'],
            style_02['binary'],
            style_01['name'],
            style_02['name']
        )

if __name__ == "__main__":
    main()
