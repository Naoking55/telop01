#!/usr/bin/env python3
"""
変換プログラムのテスト：異なる色のPRSLを作成して変換
"""

import sys
sys.path.insert(0, '/home/user/telop01')

from test_prsl_conversion import parse_prsl, Style
from prsl_to_prtextstyle_converter import convert_prsl_to_prtextstyle
import copy

def create_modified_prsl():
    """
    元のPRSLファイルを読み込んで、色だけ変更したバージョンを作成
    """

    print("="*80)
    print("テスト用PRSLファイル作成（色を変更）")
    print("="*80)

    # 元のPRSLを読み込み
    original_styles = parse_prsl("/tmp/10styles.prsl")

    # 色を変更
    modified_styles = []
    test_colors = [
        (255, 0, 0),      # 赤
        (0, 255, 0),      # 緑
        (0, 0, 255),      # 青
        (255, 255, 0),    # 黄
        (255, 0, 255),    # マゼンタ
        (0, 255, 255),    # シアン
        (128, 128, 128),  # グレー
        (255, 128, 0),    # オレンジ
        (128, 0, 255),    # 紫
        (0, 128, 255),    # 水色
    ]

    print(f"\n元のスタイル → 変更後:")
    for i, style in enumerate(original_styles):
        # ディープコピー
        new_style = copy.deepcopy(style)

        # 色を変更
        if i < len(test_colors):
            new_r, new_g, new_b = test_colors[i]
            old_r, old_g, old_b = style.fill.r, style.fill.g, style.fill.b

            new_style.fill.r = new_r
            new_style.fill.g = new_g
            new_style.fill.b = new_b

            print(f"  スタイル {i+1}: RGB({old_r:3d}, {old_g:3d}, {old_b:3d}) → RGB({new_r:3d}, {new_g:3d}, {new_b:3d})")

        modified_styles.append(new_style)

    # PRSLファイルとして保存（XMLフォーマット）
    output_path = "/tmp/test_modified_colors.prsl"

    # 簡易的なPRSL XMLを生成
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<stylelist>']

    for i, style in enumerate(modified_styles):
        xml_lines.append(f'  <styleblock name="{style.name}" id="{i+1}">')
        xml_lines.append('    <fill>')
        xml_lines.append(f'      <color rgb="{style.fill.r} {style.fill.g} {style.fill.b}"/>')
        xml_lines.append('    </fill>')
        # 他のパラメータは省略（変換プログラムは色のみ変更するため）
        xml_lines.append('  </styleblock>')

    xml_lines.append('</stylelist>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))

    print(f"\n✓ テスト用PRSLファイル作成: {output_path}")

    # 変換を実行
    print(f"\n{'='*80}")
    print("変換実行")
    print('='*80)

    output_prtextstyle = "/home/user/telop01/test_different_colors.prtextstyle"

    # 注意: 実際のPRSLパーサーが使えないので、直接Styleオブジェクトを使用
    # 代わりに元のPRSLを使用して、バイナリ変更関数を直接呼び出す必要がある

    print("\n注意: このテストは簡易版です")
    print("実際の変換には、完全なPRSLパーサーが必要です")

def main():
    create_modified_prsl()

    # 実際の変換は、完全なPRSL形式が必要なのでスキップ
    print(f"\n完全な変換のためには:")
    print(f"  1. 正しいPRSL形式のファイルを用意")
    print(f"  2. python3 prsl_to_prtextstyle_converter.py <prsl> <output>")
    print(f"\nデモ: 手動で色を変更した例を作成します...")

    # 代わりに、既存のコンバータを使って、テンプレートの最初のスタイルを変更
    from prsl_to_prtextstyle_converter import modify_fill_color_in_binary, MARKER
    import base64
    import re

    # テンプレートファイルを読み込み
    with open('/tmp/10styles.prtextstyle', 'r', encoding='utf-8') as f:
        content = f.read()

    # 最初のバイナリを抽出
    pattern = r'(<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">)([A-Za-z0-9+/=\s]+)(</StartKeyframeValue>)'
    matches = list(re.finditer(pattern, content, re.DOTALL))

    if matches:
        first_match = matches[0]
        original_b64 = first_match.group(2).replace('\n', '').replace(' ', '').replace('\t', '')
        original_binary = base64.b64decode(original_b64)

        # 元: RGB(0, 114, 255) → 新: RGB(255, 0, 0) 赤
        modified_binary = modify_fill_color_in_binary(
            original_binary,
            0, 114, 255,  # 元の色
            255, 0, 0     # 赤
        )

        new_b64 = base64.b64encode(modified_binary).decode('ascii')

        # ファイルを更新
        new_content = content[:first_match.start(2)] + new_b64 + content[first_match.end(2):]

        # スタイル名も変更
        new_content = re.sub(r'(<Name>)(001)(</Name>)', r'\1RED-TEST\3', new_content, count=1)

        # 保存
        output_path = "/home/user/telop01/test_red_color.prtextstyle"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"\n✓ 赤色テストファイル作成: {output_path}")
        print(f"  最初のスタイルを RGB(0,114,255) → RGB(255,0,0) に変更")
        print(f"\nPremiereで読み込んでテストしてください！")

if __name__ == "__main__":
    main()
