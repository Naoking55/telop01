#!/usr/bin/env python3
"""
Fill色の格納パターン検証 v2
新仮説：255は省略、0は0x00として格納、それ以外はそのまま格納
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

def analyze_all_styles_v2():
    """全10スタイルを解析（新仮説で）"""

    # PRSL解析
    prsl_styles = parse_prsl("/tmp/10styles.prsl")

    # 手動変換prtextstyle解析
    editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")

    print("="*80)
    print("全10スタイルのFill色格納パターン解析 v2")
    print("新仮説：255は省略、0は0x00として格納、それ以外はそのまま")
    print("="*80)

    results = []

    for i, (prsl_style, prt_name) in enumerate(zip(prsl_styles, editor.styles.keys())):
        prt_binary = editor.get_style_binary(prt_name)

        print(f"\n[Style {i+1}] {prsl_style.name}")
        r, g, b = prsl_style.fill.r, prsl_style.fill.g, prsl_style.fill.b
        print(f"  PRSL Fill: RGB({r}, {g}, {b})")
        print(f"  Binary size: {len(prt_binary)} bytes")

        # マーカーを探す
        marker_pos = find_marker_position(prt_binary)

        if marker_pos == -1:
            print(f"  ✗ Marker not found!")
            continue

        print(f"  Marker position: 0x{marker_pos:04x}")

        # 期待されるバイト列を構築（255以外の成分を順番に）
        expected_bytes = []
        component_info = []

        if r != 255:
            expected_bytes.append(r)
            component_info.append(f"R={r}")

        if g != 255:
            expected_bytes.append(g)
            component_info.append(f"G={g}")

        if b != 255:
            expected_bytes.append(b)
            component_info.append(f"B={b}")

        print(f"  Expected components (≠255): {component_info}")
        print(f"  Expected byte sequence: {expected_bytes}")

        # マーカー直前のバイトを取得
        expected_length = len(expected_bytes)
        if expected_length > 0:
            actual_bytes = []
            for j in range(expected_length, 0, -1):
                if marker_pos - j >= 0:
                    actual_bytes.append(prt_binary[marker_pos - j])

            print(f"  Actual bytes before marker: {actual_bytes}")

            if actual_bytes == expected_bytes:
                print(f"  ✓✓✓ PERFECT MATCH!")
                results.append({'style': i+1, 'match': True})
            else:
                print(f"  ✗ NO MATCH")
                results.append({'style': i+1, 'match': False})

                # 詳細表示
                print(f"\n  Comparison:")
                for idx, (exp, act) in enumerate(zip(expected_bytes, actual_bytes)):
                    match_str = "✓" if exp == act else "✗"
                    print(f"    [{idx}] Expected: {exp:3d}, Actual: {act:3d} {match_str}")
        else:
            # 全成分が255の場合
            print(f"  All components are 255, no bytes expected before marker")
            print(f"  ✓ MATCH (empty case)")
            results.append({'style': i+1, 'match': True})

    # 結果サマリー
    print(f"\n{'='*80}")
    print("結果サマリー")
    print('='*80)

    match_count = sum(1 for r in results if r['match'])
    print(f"Match: {match_count}/{len(results)} styles")

    if match_count == len(results):
        print("\n" + "="*80)
        print("✓✓✓ パターン完全確定！ ✓✓✓")
        print("="*80)
        print("\nFill色の格納ルール:")
        print("  1. マーカー '02 00 00 00 41 61' を探す")
        print("  2. マーカーの直前に、255以外のRGB成分が順番に格納")
        print("  3. R, G, Bの順で、255の成分は省略、それ以外（0を含む）は格納")
        print("\n例:")
        print("  RGB(0, 114, 255) → [00 72]    (R=0, G=114を格納、B=255は省略)")
        print("  RGB(255, 0, 126) → [00 7e]    (R=255省略、G=0, B=126を格納)")
        print("  RGB(17, 121, 77) → [11 79 4d] (全て格納)")
        print("  RGB(255, 174, 0) → [ae 00]    (R=255省略、G=174, B=0を格納)")
        print("  RGB(255, 255, 255)→ []         (全て省略)")
    else:
        print(f"\n✗ パターンが一致しないスタイルあり: {[r['style'] for r in results if not r['match']]}")

if __name__ == "__main__":
    analyze_all_styles_v2()
