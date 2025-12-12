#!/usr/bin/env python3
"""
複数スタイルを含むprtextstyleファイルの解析ツール
100個や200個のスタイルが含まれるファイルの構造を理解する
"""

import xml.etree.ElementTree as ET
import base64
import struct
import sys
from pathlib import Path
from collections import defaultdict

def analyze_prtextstyle_file(filepath):
    """prtextstyleファイルを解析"""
    print(f"\n{'='*80}")
    print(f"解析ファイル: {filepath}")
    print(f"{'='*80}\n")

    # XMLパース
    tree = ET.parse(filepath)
    root = tree.getroot()

    # 基本情報
    print(f"📊 基本情報:")
    print(f"  - PremiereData Version: {root.get('Version')}")

    # スタイル数をカウント
    items = root.findall(".//Item")
    print(f"  - 総Item数: {len(items)}")

    # SourceTextを含むアイテムを探す
    source_text_items = []
    for item in root.iter():
        if 'SourceText' in item.tag or item.tag == 'BinaryData':
            parent = find_parent_with_name(root, item)
            if parent is not None:
                source_text_items.append(parent)

    # スタイル名を収集
    style_names = []
    root_bin = root.find(".//RootProjectItem")
    if root_bin is not None:
        items_container = root_bin.find(".//Items")
        if items_container is not None:
            for item in items_container.findall("Item"):
                obj_ref = item.get('ObjectURef')
                # このObjectURefに対応する名前を探す
                style_item = root.find(f".//*[@ObjectUID='{obj_ref}']")
                if style_item is not None:
                    name_elem = style_item.find(".//Name")
                    if name_elem is not None and name_elem.text:
                        style_names.append(name_elem.text)

    print(f"  - スタイル数: {len(style_names)}")

    # スタイル名のサンプルを表示
    if style_names:
        print(f"\n📝 スタイル名サンプル (最初の10個):")
        for i, name in enumerate(style_names[:10], 1):
            print(f"  {i:3d}. {name}")
        if len(style_names) > 10:
            print(f"  ... (他 {len(style_names) - 10} 個)")

    # BinaryDataを解析
    binary_data_elements = root.findall(".//BinaryData")
    print(f"\n🔢 バイナリデータ:")
    print(f"  - BinaryData要素数: {len(binary_data_elements)}")

    # 各BinaryDataのサイズを確認
    binary_sizes = []
    for bd in binary_data_elements:
        if bd.text:
            try:
                decoded = base64.b64decode(bd.text.strip())
                binary_sizes.append(len(decoded))
            except:
                pass

    if binary_sizes:
        print(f"  - バイナリサイズ範囲: {min(binary_sizes)} - {max(binary_sizes)} bytes")
        print(f"  - 平均サイズ: {sum(binary_sizes) // len(binary_sizes)} bytes")

        # サイズ別分布
        size_distribution = defaultdict(int)
        for size in binary_sizes:
            # 100バイト単位でグループ化
            size_group = (size // 100) * 100
            size_distribution[size_group] += 1

        print(f"\n  サイズ分布 (100バイト単位):")
        for size_group in sorted(size_distribution.keys()):
            count = size_distribution[size_group]
            bar = '█' * (count // 5 if count > 5 else 1)
            print(f"    {size_group:4d}-{size_group+99:4d} bytes: {count:3d} {bar}")

    # 最初のいくつかのスタイルのバイナリを詳細解析
    print(f"\n🔍 最初の3スタイルの詳細解析:")
    analyzed_count = 0
    for i, bd in enumerate(binary_data_elements[:3]):
        if bd.text:
            try:
                decoded = base64.b64decode(bd.text.strip())
                style_name = style_names[i] if i < len(style_names) else f"Style {i+1}"
                analyze_single_binary(decoded, style_name, i+1)
                analyzed_count += 1
            except Exception as e:
                print(f"  ⚠️ スタイル {i+1} の解析エラー: {e}")

    return {
        'filepath': filepath,
        'total_styles': len(style_names),
        'style_names': style_names,
        'binary_count': len(binary_data_elements),
        'binary_sizes': binary_sizes
    }

def find_parent_with_name(root, element):
    """名前を持つ親要素を探す"""
    for parent in root.iter():
        for child in parent:
            if child == element:
                name_elem = parent.find(".//Name")
                if name_elem is not None:
                    return parent
    return None

def analyze_single_binary(data, style_name, index):
    """単一のバイナリデータを解析"""
    print(f"\n  --- スタイル {index}: {style_name} ---")
    print(f"  サイズ: {len(data)} bytes")

    # FlatBuffersマジックナンバー確認
    if len(data) >= 12:
        magic = data[8:12]
        if magic == b'\x44\x33\x22\x11':
            print(f"  ✓ FlatBuffers形式確認")
        else:
            print(f"  ? 不明な形式: {magic.hex()}")

    # フォントサイズ (0x009c)
    if len(data) >= 0xa0:
        font_size = struct.unpack("<f", data[0x9c:0xa0])[0]
        print(f"  フォントサイズ: {font_size:.1f} pt")

    # フォント名を探す (0x00d0付近)
    font_name = extract_font_name(data)
    if font_name:
        print(f"  フォント名: {font_name}")

    # 色データを探す (RGB bytes)
    colors = find_color_patterns(data)
    if colors:
        print(f"  検出された色: {len(colors)} 個")
        for i, (offset, r, g, b) in enumerate(colors[:3], 1):
            print(f"    {i}. RGB({r:3d}, {g:3d}, {b:3d}) @ 0x{offset:04x}")

def extract_font_name(data):
    """フォント名を抽出"""
    # 0x00d0付近から文字列を探す
    start = 0x00cc
    if len(data) < start + 4:
        return None

    try:
        # 長さプレフィックス
        name_len = struct.unpack("<I", data[start:start+4])[0]
        if name_len > 0 and name_len < 100:  # 妥当な長さ
            name_start = start + 4
            if len(data) >= name_start + name_len:
                font_name = data[name_start:name_start+name_len].decode('utf-8', errors='ignore')
                # NULL文字を除去
                font_name = font_name.rstrip('\x00')
                if font_name and font_name.isprintable():
                    return font_name
    except:
        pass

    return None

def find_color_patterns(data):
    """RGB色パターンを探す"""
    colors = []
    # VTable領域をスキップ
    search_start = 0x0150

    for i in range(search_start, len(data) - 3):
        r, g, b = data[i], data[i+1], data[i+2]

        # 色として妥当そうなパターン
        # (極端に偏った値や、すべて同じ値を除外)
        if (r == 255 or g == 255 or b == 255 or
            r == 0 or g == 0 or b == 0):
            # 重複を避ける
            if not colors or i - colors[-1][0] > 10:
                colors.append((i, r, g, b))

    return colors[:5]  # 最初の5個まで

def main():
    files = [
        "prtextstyle/100 New Fonstyle.prtextstyle",
        "prtextstyle/200 New FontStyles_01.prtextstyle"
    ]

    results = []
    for filepath in files:
        if Path(filepath).exists():
            result = analyze_prtextstyle_file(filepath)
            results.append(result)
        else:
            print(f"⚠️ ファイルが見つかりません: {filepath}")

    # サマリー
    print(f"\n{'='*80}")
    print("📈 解析サマリー")
    print(f"{'='*80}\n")

    for result in results:
        filepath = Path(result['filepath']).name
        print(f"📄 {filepath}")
        print(f"  - スタイル数: {result['total_styles']}")
        print(f"  - バイナリ数: {result['binary_count']}")
        if result['binary_sizes']:
            print(f"  - サイズ範囲: {min(result['binary_sizes'])} - {max(result['binary_sizes'])} bytes")
        print()

if __name__ == "__main__":
    main()
