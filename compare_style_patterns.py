#!/usr/bin/env python3
"""
prtextstyleファイル内の全スタイルを比較分析
PRSLの色と実際の保存パターンを対比
"""

import sys
import re
import base64

MARKER = b'\x02\x00\x00\x00\x41\x61'

# PRSLから取得した期待される色（check_prsl_colors.pyの結果）
EXPECTED_COLORS = [
    ("Style 1", 0, 114, 255),
    ("Style 2", 255, 0, 126),
    ("Style 3", 18, 121, 78),
    ("Style 4", 255, 174, 0),
    ("Style 5", 255, 255, 255),
    ("Style 6", 0, 255, 210),
    ("Style 7", 255, 108, 0),
    ("Style 8", 253, 255, 0),
    ("Style 9", 255, 242, 0),
    ("Style 10", 255, 244, 162),
]

def get_color_structure(r, g, b):
    """色構造を判定（どのRGB成分が255=skipか）"""
    structure = []
    stored = []

    if r == 255:
        structure.append('R=skip')
    else:
        structure.append('R=store')
        stored.append(('R', r))

    if g == 255:
        structure.append('G=skip')
    else:
        structure.append('G=store')
        stored.append(('G', g))

    if b == 255:
        structure.append('B=skip')
    else:
        structure.append('B=store')
        stored.append(('B', b))

    return ', '.join(structure), stored

def analyze_binary_around_marker(binary, marker_pos, context=10):
    """マーカー周辺のバイナリを詳細分析"""
    start = max(0, marker_pos - context)
    end = min(len(binary), marker_pos + len(MARKER) + context)

    bytes_around = []
    for i in range(start, end):
        offset = i - marker_pos
        byte_val = binary[i]
        is_marker = marker_pos <= i < marker_pos + len(MARKER)

        bytes_around.append({
            'offset': offset,
            'value': byte_val,
            'is_marker': is_marker
        })

    return bytes_around

def compare_styles(prtextstyle_file):
    """全スタイルを比較分析"""
    print("="*80)
    print("スタイル間比較分析")
    print("="*80)

    # ファイル読み込み
    with open(prtextstyle_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # StartKeyframeValue抽出
    pattern = r'<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">([A-Za-z0-9+/=\s]+)</StartKeyframeValue>'
    matches = re.findall(pattern, content, re.DOTALL)

    print(f"\n検出: {len(matches)} エントリ\n")

    results = []

    for i, b64_text in enumerate(matches):
        if i >= len(EXPECTED_COLORS):
            break

        name, exp_r, exp_g, exp_b = EXPECTED_COLORS[i]
        structure_desc, stored_components = get_color_structure(exp_r, exp_g, exp_b)

        # Base64デコード
        b64_clean = b64_text.replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
        binary = base64.b64decode(b64_clean)

        # マーカー検索
        marker_pos = binary.find(MARKER)

        if marker_pos == -1:
            print(f"\n[{i+1}] {name}: マーカーなし")
            continue

        # マーカー周辺を分析
        around = analyze_binary_around_marker(binary, marker_pos, context=5)

        # マーカー直前のバイトを取得
        num_stored = len(stored_components)
        bytes_before_marker = []
        for j in range(num_stored):
            if marker_pos - num_stored + j >= 0:
                bytes_before_marker.append(binary[marker_pos - num_stored + j])

        # 期待される保存バイト
        expected_bytes = [val for _, val in stored_components]

        # 結果表示
        print(f"\n{'='*80}")
        print(f"[{i+1}] {name}")
        print(f"{'='*80}")
        print(f"PRSL色:      RGB({exp_r:3d}, {exp_g:3d}, {exp_b:3d})")
        print(f"色構造:      {structure_desc}")
        print(f"保存成分数:  {num_stored} バイト")
        print(f"期待バイト:  {expected_bytes}")
        print(f"実際バイト:  {bytes_before_marker}")
        print(f"マーカー位置: {marker_pos}")

        # 一致確認
        if bytes_before_marker == expected_bytes:
            print(f"結果:        ✓ 完全一致")
        else:
            print(f"結果:        ✗ 不一致")

        # マーカー周辺の詳細
        print(f"\nマーカー周辺のバイト:")
        for b in around:
            marker_flag = "←MARKER" if b['is_marker'] else ""
            offset_str = f"[{b['offset']:+3d}]"
            print(f"  {offset_str} 0x{b['value']:02x} ({b['value']:3d}) {marker_flag}")

        results.append({
            'index': i + 1,
            'name': name,
            'expected_rgb': (exp_r, exp_g, exp_b),
            'structure': structure_desc,
            'num_stored': num_stored,
            'expected_bytes': expected_bytes,
            'actual_bytes': bytes_before_marker,
            'match': bytes_before_marker == expected_bytes,
            'marker_pos': marker_pos
        })

    # サマリー
    print(f"\n{'='*80}")
    print("サマリー")
    print(f"{'='*80}")

    match_count = sum(1 for r in results if r['match'])
    print(f"\n一致数: {match_count}/{len(results)}")

    # 構造別グループ化
    from collections import defaultdict
    by_structure = defaultdict(list)
    for r in results:
        by_structure[r['structure']].append(r)

    print(f"\n色構造別:")
    for struct, items in sorted(by_structure.items()):
        print(f"\n  {struct}:")
        for item in items:
            match_str = "✓" if item['match'] else "✗"
            print(f"    [{item['index']}] {item['name']:20s} {match_str}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python3 compare_style_patterns.py <prtextstyle_file>")
        sys.exit(1)

    compare_styles(sys.argv[1])
