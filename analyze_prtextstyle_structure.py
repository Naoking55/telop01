#!/usr/bin/env python3
"""
実際のprtextstyleファイルの構造を解析
どのバイト位置にどのパラメータがあるか特定
"""

import base64
import struct
import xml.etree.ElementTree as ET

def extract_style_binaries(filepath):
    """prtextstyleファイルから全スタイルのバイナリを抽出"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    styles = {}

    for style_item in root.findall('.//StyleProjectItem'):
        # スタイル名取得
        name_elem = style_item.find('.//Name')
        style_name = name_elem.text if name_elem is not None and name_elem.text else "Unknown"

        # バイナリ取得
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
        if binary_elem is not None and binary_elem.text:
            binary = base64.b64decode(binary_elem.text.strip())
            styles[style_name] = binary

    return styles

def find_all_floats(binary, value_range=(0.0, 1.0)):
    """バイナリ内で特定範囲のfloat値を探す"""
    found = []
    for offset in range(0, len(binary) - 3, 1):  # 1バイトずつ探索
        try:
            val = struct.unpack('<f', binary[offset:offset+4])[0]
            if value_range[0] <= val <= value_range[1]:
                found.append((offset, val))
        except:
            pass
    return found

def analyze_file(filepath):
    """ファイル全体を解析"""
    print("="*80)
    print(f"Analyzing: {filepath}")
    print("="*80)

    styles = extract_style_binaries(filepath)

    print(f"\nFound {len(styles)} styles:")
    for name in styles.keys():
        print(f"  - {name}")

    if not styles:
        print("No styles found!")
        return

    # 最初のスタイルを詳細解析
    style_name = list(styles.keys())[0]
    binary = styles[style_name]

    print(f"\n{'='*80}")
    print(f"Detailed Analysis: {style_name}")
    print(f"Binary size: {len(binary)} bytes")
    print('='*80)

    # 0.0-1.0 の範囲のfloatを探す（色の可能性）
    print("\nSearching for float values in range [0.0, 1.0] (potential colors):")
    floats = find_all_floats(binary, (0.0, 1.0))

    # 連続する4つのfloat（RGBA候補）を探す
    print("\nPotential RGBA color blocks (4 consecutive floats in [0.0, 1.0]):")
    i = 0
    rgba_candidates = []
    while i < len(floats) - 3:
        offset1, val1 = floats[i]
        offset2, val2 = floats[i+1]
        offset3, val3 = floats[i+2]
        offset4, val4 = floats[i+3]

        # 4バイトずつ連続しているか確認
        if offset2 == offset1 + 4 and offset3 == offset2 + 4 and offset4 == offset3 + 4:
            rgba = (val1, val2, val3, val4)
            rgba_255 = tuple(int(v * 255) for v in rgba)
            rgba_candidates.append((offset1, rgba, rgba_255))
            print(f"  0x{offset1:04x}: RGBA({val1:.3f}, {val2:.3f}, {val3:.3f}, {val4:.3f}) = RGB{rgba_255}")
            i += 4
        else:
            i += 1

    # -50.0 ~ 50.0 の範囲のfloat（Shadow offset候補）
    print("\nSearching for float values in range [-50.0, 50.0] (potential shadow offsets):")
    shadow_floats = find_all_floats(binary, (-50.0, 50.0))

    # ペアで連続するもの（X,Y候補）
    print("\nPotential Shadow X,Y pairs:")
    for i in range(len(shadow_floats) - 1):
        offset1, val1 = shadow_floats[i]
        offset2, val2 = shadow_floats[i+1]

        if offset2 == offset1 + 4:  # 連続している
            if abs(val1) > 0.1 or abs(val2) > 0.1:  # ゼロではない
                print(f"  0x{offset1:04x}: X={val1:.2f}, Y={val2:.2f}")

    # 0-100の範囲（Blur候補）
    print("\nSearching for float values in range [0.0, 100.0] (potential blur/size):")
    blur_floats = find_all_floats(binary, (0.0, 100.0))

    # 先頭100個だけ表示
    for offset, val in blur_floats[:20]:
        print(f"  0x{offset:04x}: {val:.2f}")

    return binary, rgba_candidates

# メインのテストファイルを解析
print("\n" + "="*80)
print("ANALYSIS 1: Simple style (白・ストローク無し)")
print("="*80)
binary1, rgba1 = analyze_file("prtextstyle/白・ストローク無し.prtextstyle")

print("\n\n" + "="*80)
print("ANALYSIS 2: Style with stroke (白・エッジ黄)")
print("="*80)
binary2, rgba2 = analyze_file("prtextstyle/白・エッジ黄.prtextstyle")

# 2つのバイナリを比較
if binary1 and binary2:
    print("\n\n" + "="*80)
    print("BINARY COMPARISON: Finding differences")
    print("="*80)

    min_len = min(len(binary1), len(binary2))
    diffs = []

    for i in range(min_len):
        if binary1[i] != binary2[i]:
            diffs.append(i)

    print(f"\nSize: {len(binary1)} vs {len(binary2)} bytes")
    print(f"Differences: {len(diffs)} bytes")

    if diffs:
        print(f"\nFirst 20 difference locations:")
        for i in diffs[:20]:
            print(f"  0x{i:04x}: 0x{binary1[i]:02x} vs 0x{binary2[i]:02x}")
