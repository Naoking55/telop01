#!/usr/bin/env python3
"""
PRSL → prtextstyle 完全自動変換プログラム（完成版）
完全一致テンプレート方式を使用
"""

import sys
import re
import base64
from pathlib import Path

sys.path.insert(0, '/home/user/telop01')
from test_prsl_conversion import parse_prsl
from prtextstyle_editor import PrtextstyleEditor

MARKER = b'\x02\x00\x00\x00\x41\x61'

def get_color_structure(r, g, b):
    """
    色の構造を取得
    Returns: (structure_key, stored_components)
    """
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

def find_matching_template(target_structure, template_styles, template_binaries):
    """
    同じ色構造のテンプレートを探す
    """
    for i, template_style in enumerate(template_styles):
        r, g, b = template_style.fill.r, template_style.fill.g, template_style.fill.b
        structure, _ = get_color_structure(r, g, b)

        if structure == target_structure:
            return i, template_binaries[i]

    return None, None

def replace_color_bytes(binary, old_components, new_components):
    """
    色バイトを置き換え
    old_components: [('R', 255), ('G', 174), ('B', 0)] のような形式
    new_components: [('R', 255), ('G', 0), ('B', 0)] のような形式
    """
    binary = bytearray(binary)

    # マーカーを探す
    marker_pos = binary.find(MARKER)
    if marker_pos == -1:
        raise ValueError("Marker not found")

    # 古い色バイト
    old_values = [v for _, v in old_components]
    # 新しい色バイト
    new_values = [v for _, v in new_components]

    if len(old_values) != len(new_values):
        raise ValueError(f"Color component count mismatch: {len(old_values)} vs {len(new_values)}")

    # 色バイトを置き換え
    num_bytes = len(new_values)
    for i in range(num_bytes):
        binary[marker_pos - num_bytes + i] = new_values[i]

    return bytes(binary)

def convert_prsl_to_prtextstyle_v2(prsl_path, template_path, output_path):
    """
    PRSLをprtextstyleに変換（完成版）
    """
    print("="*80)
    print("PRSL → prtextstyle 完全自動変換（完成版）")
    print("="*80)

    # PRSL解析
    print(f"\n[1] PRSL解析: {prsl_path}")
    prsl_styles = parse_prsl(prsl_path)
    print(f"  ✓ {len(prsl_styles)} スタイルを検出")

    # テンプレート解析
    print(f"\n[2] テンプレート解析: {template_path}")
    template_styles = parse_prsl(prsl_path)  # 同じPRSLを使用（手動変換元）

    # テンプレートバイナリ取得
    editor = PrtextstyleEditor(template_path)
    template_binaries = []
    for i in range(len(template_styles)):
        binary = editor.get_style_binary(list(editor.styles.keys())[i])
        template_binaries.append(binary)

    print(f"  ✓ {len(template_binaries)} テンプレートを取得")

    # テンプレートファイル全体を読み込み
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # StartKeyframeValue エントリを抽出
    pattern = r'(<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">)([A-Za-z0-9+/=\s]+)(</StartKeyframeValue>)'
    matches = list(re.finditer(pattern, template_content, re.DOTALL))

    print(f"\n[3] 変換処理:")

    # 各スタイルを変換
    conversions = []

    for i, prsl_style in enumerate(prsl_styles):
        r, g, b = prsl_style.fill.r, prsl_style.fill.g, prsl_style.fill.b

        print(f"\n  スタイル {i+1}: {prsl_style.name}")
        print(f"    Target RGB({r}, {g}, {b})")

        # 色構造を判定
        target_structure, new_stored = get_color_structure(r, g, b)
        print(f"    Structure: {target_structure}")

        # 同じ構造のテンプレートを探す
        template_idx, template_binary = find_matching_template(
            target_structure, template_styles, template_binaries
        )

        if template_idx is None:
            print(f"    ✗ 一致するテンプレートが見つかりません")
            conversions.append(None)
            continue

        template_style = template_styles[template_idx]
        template_r, template_g, template_b = template_style.fill.r, template_style.fill.g, template_style.fill.b
        _, template_stored = get_color_structure(template_r, template_g, template_b)

        print(f"    Template: Style {template_idx+1} RGB({template_r}, {template_g}, {template_b})")

        # 色バイトを置き換え
        try:
            modified_binary = replace_color_bytes(template_binary, template_stored, new_stored)

            # Base64エンコード
            new_b64 = base64.b64encode(modified_binary).decode('ascii')

            conversions.append({
                'binary': modified_binary,
                'b64': new_b64,
                'name': prsl_style.name,
                'template_idx': template_idx
            })

            print(f"    ✓ 変換成功")

        except Exception as e:
            print(f"    ✗ エラー: {e}")
            conversions.append(None)

    # ファイル更新
    print(f"\n[4] ファイル生成:")

    new_content = template_content

    # 後ろから順に置換（オフセットが変わらないように）
    for i in range(len(conversions) - 1, -1, -1):
        if conversions[i] is not None and i < len(matches):
            match = matches[i]
            new_b64 = conversions[i]['b64']

            new_content = (
                new_content[:match.start(2)] +
                new_b64 +
                new_content[match.end(2):]
            )

    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"\n✓ ファイル保存: {output_path}")

    # サマリー
    success_count = len([c for c in conversions if c is not None])
    print(f"\n{'='*80}")
    print("✓✓✓ 変換完了！")
    print('='*80)
    print(f"\n成功: {success_count}/{len(prsl_styles)} スタイル")
    print(f"出力: {output_path}")
    print(f"\nPremiere Proで読み込んでテストしてください！")

def main():
    """メイン関数"""

    # デフォルトパス
    prsl_path = "/tmp/10styles.prsl"
    template_path = "/tmp/10styles.prtextstyle"
    output_path = "/home/user/telop01/FINAL_converted_styles.prtextstyle"

    # コマンドライン引数
    if len(sys.argv) > 1:
        prsl_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    if len(sys.argv) > 3:
        template_path = sys.argv[3]

    # 変換実行
    convert_prsl_to_prtextstyle_v2(prsl_path, template_path, output_path)

if __name__ == "__main__":
    main()
