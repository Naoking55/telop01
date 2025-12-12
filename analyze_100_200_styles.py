#!/usr/bin/env python3
"""
100個/200個のスタイルを含むprtextstyleファイルの完全解析
"""

import xml.etree.ElementTree as ET
import base64
import struct
from pathlib import Path
from collections import defaultdict, Counter

def extract_font_name(data, start_offset=0x00cc):
    """フォント名を抽出"""
    if len(data) < start_offset + 4:
        return None

    try:
        name_len = struct.unpack("<I", data[start_offset:start_offset+4])[0]
        if 0 < name_len < 100:
            name_start = start_offset + 4
            if len(data) >= name_start + name_len:
                font_name = data[name_start:name_start+name_len].decode('utf-8', errors='ignore')
                font_name = font_name.rstrip('\x00')
                if font_name and font_name.isprintable():
                    return font_name
    except:
        pass

    return None

def find_rgb_colors(data):
    """RGB色を探す（VTable領域をスキップ）"""
    colors = []
    search_start = 0x0150

    for i in range(search_start, min(len(data) - 3, search_start + 200)):
        r, g, b = data[i], data[i+1], data[i+2]

        # 特定の色パターンを検出
        if (r, g, b) in [(255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255),
                         (255, 255, 0), (255, 0, 255), (0, 255, 255), (0, 0, 0)]:
            if not colors or i - colors[-1][0] > 10:
                colors.append((i, r, g, b))

    return colors

def has_stroke(data):
    """ストロークの有無を判定（簡易版）"""
    # ファイルサイズで判定（暫定）
    if len(data) > 460:
        return True
    return False

def has_gradient(data):
    """グラデーションの有無を判定（簡易版）"""
    # ファイルサイズで判定（暫定）
    if len(data) > 600:
        return True
    return False

def analyze_style_binary(data, style_name):
    """単一スタイルのバイナリを解析"""
    info = {
        'name': style_name,
        'size': len(data),
        'font_size': None,
        'font_name': None,
        'colors': [],
        'has_stroke': has_stroke(data),
        'has_gradient': has_gradient(data)
    }

    # FlatBuffersマジックナンバー確認
    if len(data) >= 12:
        magic = data[8:12]
        info['is_flatbuffers'] = (magic == b'\x44\x33\x22\x11')

    # フォントサイズ
    if len(data) >= 0xa0:
        try:
            info['font_size'] = struct.unpack("<f", data[0x9c:0xa0])[0]
        except:
            pass

    # フォント名
    info['font_name'] = extract_font_name(data)

    # 色
    info['colors'] = find_rgb_colors(data)

    return info

def analyze_prtextstyle_multi(filepath):
    """複数スタイルを含むprtextstyleファイルを解析"""
    print(f"\n{'='*80}")
    print(f"📄 {Path(filepath).name}")
    print(f"{'='*80}\n")

    tree = ET.parse(filepath)
    root = tree.getroot()

    # StyleProjectItemを取得
    style_items = root.findall('.//StyleProjectItem')
    print(f"スタイル数: {len(style_items)}")

    # 各スタイルを解析
    style_data = []

    for idx, style_item in enumerate(style_items):
        # スタイル名
        name_elem = style_item.find('.//Name')
        style_name = name_elem.text if name_elem is not None else f"Style_{idx+1}"

        # Component参照を取得
        component_ref_elem = style_item.find('.//Component[@ObjectRef]')
        if component_ref_elem is None:
            continue

        component_ref = component_ref_elem.get('ObjectRef')

        # VideoFilterComponentを探す
        vfc = root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")
        if vfc is None:
            continue

        # 最初のParam（Index="0"、Source Text）を取得
        first_param_ref = vfc.find(".//Param[@Index='0']")
        if first_param_ref is None:
            continue

        param_obj_ref = first_param_ref.get('ObjectRef')

        # ArbVideoComponentParamを探す
        arb_param = root.find(f".//ArbVideoComponentParam[@ObjectID='{param_obj_ref}']")
        if arb_param is None:
            continue

        # Base64バイナリを取得
        binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
        if binary_elem is None or not binary_elem.text:
            continue

        # デコード
        try:
            binary_data = base64.b64decode(binary_elem.text.strip())
            info = analyze_style_binary(binary_data, style_name)
            style_data.append(info)
        except Exception as e:
            print(f"⚠️ {style_name} の解析エラー: {e}")

    return style_data

def print_statistics(all_styles):
    """統計情報を表示"""
    print(f"\n{'='*80}")
    print("📊 統計サマリー")
    print(f"{'='*80}\n")

    # 総数
    print(f"総スタイル数: {len(all_styles)}")

    # サイズ分布
    sizes = [s['size'] for s in all_styles]
    print(f"\nバイナリサイズ:")
    print(f"  最小: {min(sizes)} bytes")
    print(f"  最大: {max(sizes)} bytes")
    print(f"  平均: {sum(sizes) // len(sizes)} bytes")

    # サイズ分布ヒストグラム
    size_ranges = defaultdict(int)
    for size in sizes:
        range_key = (size // 50) * 50
        size_ranges[range_key] += 1

    print(f"\n  サイズ分布 (50バイト単位):")
    for range_start in sorted(size_ranges.keys())[:15]:
        count = size_ranges[range_start]
        bar = '█' * min(count // 3, 40)
        print(f"    {range_start:4d}-{range_start+49:4d} bytes: {count:3d} {bar}")

    # フォント名分布
    font_names = [s['font_name'] for s in all_styles if s['font_name']]
    if font_names:
        font_counter = Counter(font_names)
        print(f"\n使用フォント Top 10:")
        for font, count in font_counter.most_common(10):
            print(f"  {font:30s}: {count:3d} スタイル")

    # 色の分布
    all_colors = []
    for s in all_styles:
        for _, r, g, b in s['colors']:
            all_colors.append((r, g, b))

    if all_colors:
        color_counter = Counter(all_colors)
        print(f"\n使用色 Top 10:")
        for (r, g, b), count in color_counter.most_common(10):
            print(f"  RGB({r:3d}, {g:3d}, {b:3d}): {count:3d} スタイル")

    # ストローク/グラデーションの割合
    stroke_count = sum(1 for s in all_styles if s['has_stroke'])
    gradient_count = sum(1 for s in all_styles if s['has_gradient'])

    print(f"\nスタイル特徴:")
    print(f"  ストロークあり: {stroke_count} ({stroke_count*100//len(all_styles)}%)")
    print(f"  グラデーション:  {gradient_count} ({gradient_count*100//len(all_styles)}%)")

def print_samples(styles, num_samples=5):
    """サンプルを表示"""
    print(f"\n{'='*80}")
    print(f"📝 スタイルサンプル (最初の{num_samples}個)")
    print(f"{'='*80}\n")

    for i, style in enumerate(styles[:num_samples], 1):
        print(f"{i}. {style['name']}")
        print(f"   サイズ: {style['size']} bytes")
        if style['font_name']:
            print(f"   フォント: {style['font_name']}")
        if style['font_size']:
            print(f"   サイズ: {style['font_size']:.1f} pt")
        if style['colors']:
            colors_str = ", ".join([f"RGB({r},{g},{b})" for _, r, g, b in style['colors'][:2]])
            print(f"   色: {colors_str}")
        features = []
        if style['has_stroke']:
            features.append("ストローク")
        if style['has_gradient']:
            features.append("グラデ")
        if features:
            print(f"   特徴: {', '.join(features)}")
        print()

def main():
    files = [
        "prtextstyle/100 New Fonstyle.prtextstyle",
        "prtextstyle/200 New FontStyles_01.prtextstyle"
    ]

    all_styles = []

    for filepath in files:
        if not Path(filepath).exists():
            print(f"⚠️ ファイルが見つかりません: {filepath}")
            continue

        styles = analyze_prtextstyle_multi(filepath)
        all_styles.extend(styles)

        # ファイルごとのサンプル表示
        print_samples(styles, num_samples=3)

    # 全体統計
    if all_styles:
        print_statistics(all_styles)

    print(f"\n✅ 解析完了: {len(all_styles)} スタイル")

if __name__ == "__main__":
    main()
