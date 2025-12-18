#!/usr/bin/env python3
"""
全10スタイルでFill色の格納パターンを検証
仮説：0または255の成分は省略され、それ以外の成分だけが格納される
"""

import sys
sys.path.insert(0, '/home/user/telop01')

from test_prsl_conversion import parse_prsl
from prtextstyle_editor import PrtextstyleEditor

def find_marker_position(binary, marker=b'\x02\x00\x00\x00\x41\x61'):
    """マーカーの位置を探す"""
    try:
        return binary.index(marker)
    except ValueError:
        return -1

def analyze_all_styles():
    """全10スタイルを解析してパターンを見つける"""

    # PRSL解析
    prsl_styles = parse_prsl("/tmp/10styles.prsl")

    # 手動変換prtextstyle解析
    editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")

    print("="*80)
    print("全10スタイルのFill色格納パターン解析")
    print("="*80)

    results = []

    for i, (prsl_style, prt_name) in enumerate(zip(prsl_styles, editor.styles.keys())):
        prt_binary = editor.get_style_binary(prt_name)

        print(f"\n[Style {i+1}] {prsl_style.name}")
        print(f"  PRSL Fill: RGB({prsl_style.fill.r}, {prsl_style.fill.g}, {prsl_style.fill.b})")
        print(f"  Binary size: {len(prt_binary)} bytes")

        # マーカーを探す
        marker_pos = find_marker_position(prt_binary)

        if marker_pos == -1:
            print(f"  ✗ Marker not found!")
            continue

        print(f"  Marker position: 0x{marker_pos:04x}")

        # マーカーの直前のバイトを確認（最大3バイト前まで）
        bytes_before = []
        for j in range(1, 10):  # 最大9バイト前まで確認
            if marker_pos - j >= 0:
                bytes_before.append(prt_binary[marker_pos - j])
            else:
                break

        bytes_before.reverse()  # 正しい順序に

        print(f"  Bytes before marker: {[f'{b:3d}' for b in bytes_before[-5:]]}")

        # RGB成分と比較
        r, g, b = prsl_style.fill.r, prsl_style.fill.g, prsl_style.fill.b

        # 非0かつ非255の成分だけを抽出
        non_trivial_components = []
        component_names = []
        if 0 < r < 255:
            non_trivial_components.append(r)
            component_names.append('R')
        if 0 < g < 255:
            non_trivial_components.append(g)
            component_names.append('G')
        if 0 < b < 255:
            non_trivial_components.append(b)
            component_names.append('B')

        print(f"  Non-trivial components (0 < x < 255): {list(zip(component_names, non_trivial_components))}")

        # マーカー直前のバイトと比較
        expected_length = len(non_trivial_components)
        actual_bytes = bytes_before[-expected_length:] if expected_length > 0 else []

        print(f"  Expected bytes before marker: {non_trivial_components}")
        print(f"  Actual bytes before marker:   {actual_bytes}")

        if actual_bytes == non_trivial_components:
            print(f"  ✓ MATCH! Pattern confirmed!")
            results.append({'style': i+1, 'match': True})
        else:
            print(f"  ✗ NO MATCH")
            results.append({'style': i+1, 'match': False})

            # 詳しく調べる
            print(f"\n  Detailed hex dump around marker:")
            start = max(0, marker_pos - 20)
            for offset in range(start, marker_pos + 6):
                marker = " <-- MARKER" if offset == marker_pos else ""
                print(f"    0x{offset:04x}: {prt_binary[offset]:3d} (0x{prt_binary[offset]:02x}){marker}")

    # 結果サマリー
    print(f"\n{'='*80}")
    print("結果サマリー")
    print('='*80)

    match_count = sum(1 for r in results if r['match'])
    print(f"Match: {match_count}/{len(results)} styles")

    if match_count == len(results):
        print("\n✓✓✓ パターン確定！ ✓✓✓")
        print("\nFill色の格納ルール:")
        print("  1. マーカー '02 00 00 00 41 61' を探す")
        print("  2. マーカーの直前に非0かつ非255の成分が順番に格納されている")
        print("  3. 0または255の成分は省略される（圧縮）")
        print("\n例:")
        print("  RGB(0, 114, 255) → [114] のみ格納（G成分）")
        print("  RGB(255, 0, 126) → [126] のみ格納（B成分）")
        print("  RGB(17, 121, 77) → [17, 121, 77] 全て格納")
    else:
        print(f"\n✗ パターンが一致しないスタイルあり: {[r['style'] for r in results if not r['match']]}")

if __name__ == "__main__":
    analyze_all_styles()
