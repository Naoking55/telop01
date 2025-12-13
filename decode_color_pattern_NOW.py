#!/usr/bin/env python3
"""
今すぐ色パターンを解明する
仮説：同じ色構造（どの成分が255か）なら同じパターンバイトが使える
"""

import sys
import re
import base64
sys.path.insert(0, '/home/user/telop01')

from test_prsl_conversion import parse_prsl
from prtextstyle_editor import PrtextstyleEditor

def create_red_test_from_style2():
    """
    Style 2 (RGB(255, 0, 126)) をベースに赤 RGB(255, 0, 0) を作成
    同じ構造: R=255(skip), G=stored, B=stored
    """

    print("="*80)
    print("仮説検証：同じ色構造なら同じパターンで動作するか？")
    print("="*80)

    # 手動変換ファイルからStyle 2を取得
    editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")
    style2_binary = editor.get_style_binary(list(editor.styles.keys())[1])  # Style 2

    print(f"\nStyle 2 (ベース):")
    print(f"  RGB(255, 0, 126)")
    print(f"  構造: R=skip, G=stored, B=stored")
    print(f"  色バイト: [0, 126]")

    # マーカーを探す
    marker = b'\x02\x00\x00\x00\x41\x61'
    marker_pos = style2_binary.find(marker)

    print(f"\n  Marker at: 0x{marker_pos:04x}")

    # 色バイトを確認
    color_bytes = style2_binary[marker_pos-2:marker_pos]
    print(f"  Actual color bytes: {list(color_bytes)}")

    # パターン領域を確認
    pattern_area = style2_binary[marker_pos-16:marker_pos-8]
    print(f"  Pattern area: {' '.join(f'{b:02x}' for b in pattern_area)}")

    # 赤に変更: RGB(255, 0, 0)
    # 構造は同じ: R=skip, G=stored, B=stored
    # 色バイト: [0, 126] → [0, 0]

    print(f"\n目標: RGB(255, 0, 0) 赤")
    print(f"  構造: R=skip, G=stored, B=stored (Style 2と同じ！)")
    print(f"  色バイト: [0, 0]")

    # バイナリを変更
    modified_binary = bytearray(style2_binary)
    modified_binary[marker_pos-2] = 0  # G=0
    modified_binary[marker_pos-1] = 0  # B=0

    print(f"\n変更内容:")
    print(f"  色バイトのみ変更: [0, 126] → [0, 0]")
    print(f"  パターン領域は変更なし（同じ構造なので不要）")

    # ファイルとして保存
    # 手動変換ファイル全体を読み込み
    with open('/tmp/10styles.prtextstyle', 'r', encoding='utf-8') as f:
        content = f.read()

    # Style 2のバイナリを置換
    pattern = r'(<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">)([A-Za-z0-9+/=\s]+)(</StartKeyframeValue>)'
    matches = list(re.finditer(pattern, content, re.DOTALL))

    # 2番目のスタイル（Style 2）を置換
    if len(matches) >= 2:
        match = matches[1]  # Style 2
        new_b64 = base64.b64encode(bytes(modified_binary)).decode('ascii')

        new_content = content[:match.start(2)] + new_b64 + content[match.end(2):]

        # スタイル名も変更
        # 2番目のNameタグを探して変更
        name_pattern = r'<Name>(\d+)</Name>'
        name_matches = list(re.finditer(name_pattern, new_content))
        if len(name_matches) >= 2:
            name_match = name_matches[1]
            new_content = (
                new_content[:name_match.start(1)] +
                'RED-TEST-RGB(255,0,0)' +
                new_content[name_match.end(1):]
            )

        # 保存
        output_path = '/home/user/telop01/test_RED_from_style2_pattern.prtextstyle'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"\n✓ テストファイル作成: {output_path}")
        print(f"\n【重要】このファイルがPremiereで赤く表示されれば：")
        print(f"  → 同じ色構造なら同じパターンで動作する証明！")
        print(f"  → テンプレートマッチングで完全自動変換可能！")
        print(f"\nPremiereでテストしてください！")

def analyze_all_patterns():
    """
    全スタイルのパターンを整理して表示
    """

    print(f"\n{'='*80}")
    print("全スタイルの色構造とパターン対応表")
    print('='*80)

    prsl_styles = parse_prsl("/tmp/10styles.prsl")
    editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")

    patterns = {}  # 色構造 -> (パターンバイト, スタイル番号)

    for i in range(len(prsl_styles)):
        prsl = prsl_styles[i]
        binary = editor.get_style_binary(list(editor.styles.keys())[i])

        r, g, b = prsl.fill.r, prsl.fill.g, prsl.fill.b

        # 色構造を識別
        structure = (
            'R=skip' if r == 255 else 'R=store',
            'G=skip' if g == 255 else 'G=store',
            'B=skip' if b == 255 else 'B=store'
        )
        structure_key = ', '.join(structure)

        # マーカー位置
        marker = b'\x02\x00\x00\x00\x41\x61'
        marker_pos = binary.find(marker)

        if marker_pos != -1:
            # パターン領域
            pattern_area = binary[marker_pos-16:marker_pos-8]
            pattern_hex = ' '.join(f'{b:02x}' for b in pattern_area)

            if structure_key not in patterns:
                patterns[structure_key] = []
            patterns[structure_key].append((pattern_hex, i+1, (r, g, b)))

    # 表示
    print(f"\n色構造ごとのパターン:")
    for struct, items in sorted(patterns.items()):
        print(f"\n【{struct}】")
        for pattern, style_num, rgb in items:
            print(f"  Style {style_num}: RGB{rgb}")
            print(f"    Pattern: {pattern}")

        # 同じ構造内でパターンが一致するか確認
        unique_patterns = set(p for p, _, _ in items)
        if len(unique_patterns) == 1:
            print(f"  ✓ 全て同じパターン！")
        else:
            print(f"  ✗ パターンが異なる（{len(unique_patterns)}種類）")

if __name__ == "__main__":
    create_red_test_from_style2()
    analyze_all_patterns()
