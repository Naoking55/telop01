#!/usr/bin/env python3
"""
PRSL → prtextstyle 完全自動変換プログラム
手動変換ファイルをテンプレートとして使用し、PRSLのパラメータでバイナリを更新
"""

import sys
import re
import base64
from pathlib import Path

sys.path.insert(0, '/home/user/telop01')
from test_prsl_conversion import parse_prsl

MARKER = b'\x02\x00\x00\x00\x41\x61'

def modify_fill_color_in_binary(binary, old_r, old_g, old_b, new_r, new_g, new_b):
    """
    バイナリ内のFill色を変更

    Args:
        binary: 元のバイナリデータ
        old_r, old_g, old_b: 元のRGB値
        new_r, new_g, new_b: 新しいRGB値

    Returns:
        修正されたバイナリデータ
    """
    binary = bytearray(binary)

    # マーカーを探す
    marker_pos = binary.find(MARKER)
    if marker_pos == -1:
        raise ValueError("Marker not found in binary")

    # 元の色バイト数を計算
    old_color_bytes = []
    if old_r != 255:
        old_color_bytes.append(old_r)
    if old_g != 255:
        old_color_bytes.append(old_g)
    if old_b != 255:
        old_color_bytes.append(old_b)

    # 新しい色バイト列を作成
    new_color_bytes = []
    if new_r != 255:
        new_color_bytes.append(new_r)
    if new_g != 255:
        new_color_bytes.append(new_g)
    if new_b != 255:
        new_color_bytes.append(new_b)

    old_len = len(old_color_bytes)
    new_len = len(new_color_bytes)

    if old_len == new_len:
        # 同じ長さなら単純に置き換え
        for i, byte_val in enumerate(new_color_bytes):
            binary[marker_pos - new_len + i] = byte_val
    else:
        # 長さが異なる場合は挿入/削除
        # 古いバイトを削除
        del binary[marker_pos - old_len:marker_pos]
        # 新しいバイトを挿入
        for i, byte_val in enumerate(new_color_bytes):
            binary.insert(marker_pos - old_len + i, byte_val)

    return bytes(binary)

def convert_prsl_to_prtextstyle(prsl_path, template_path, output_path):
    """
    PRSLファイルをprtextstyleに変換

    Args:
        prsl_path: 入力PRSLファイルパス
        template_path: テンプレートprtextstyleファイルパス（手動変換ファイル）
        output_path: 出力prtextstyleファイルパス
    """

    print("="*80)
    print("PRSL → prtextstyle 自動変換")
    print("="*80)

    # PRSLを解析
    print(f"\n[1] PRSL解析: {prsl_path}")
    prsl_styles = parse_prsl(prsl_path)
    print(f"  ✓ {len(prsl_styles)} スタイルを検出")

    # テンプレートファイルを読み込み
    print(f"\n[2] テンプレート読み込み: {template_path}")
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"  ✓ {len(content)} 文字")

    # StartKeyframeValueエントリを抽出
    pattern = r'(<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">)([A-Za-z0-9+/=\s]+)(</StartKeyframeValue>)'
    matches = list(re.finditer(pattern, content, re.DOTALL))

    print(f"\n[3] バイナリエントリ検出: {len(matches)} 個")

    if len(matches) != len(prsl_styles):
        print(f"  ✗ 警告: PRSL={len(prsl_styles)}スタイル、テンプレート={len(matches)}エントリ")
        print(f"  最小値({min(len(prsl_styles), len(matches))})個まで処理します")

    # 各スタイルのバイナリを変更
    print(f"\n[4] スタイル変換:")

    # テンプレートのバイナリも解析（元の色を知るため）
    template_styles = parse_prsl(prsl_path)  # テンプレートのPRSLを使用

    modifications = []
    for i in range(min(len(prsl_styles), len(matches))):
        prsl_style = prsl_styles[i]
        match = matches[i]

        # 元のバイナリをデコード
        original_b64 = match.group(2).replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
        original_binary = base64.b64decode(original_b64)

        # テンプレートの色（PRSLから取得）
        template_style = template_styles[i]
        old_r, old_g, old_b = template_style.fill.r, template_style.fill.g, template_style.fill.b

        # PRSLの新しい色
        new_r, new_g, new_b = prsl_style.fill.r, prsl_style.fill.g, prsl_style.fill.b

        print(f"\n  スタイル {i+1}: {prsl_style.name}")
        print(f"    元の色: RGB({old_r}, {old_g}, {old_b})")
        print(f"    新しい色: RGB({new_r}, {new_g}, {new_b})")

        try:
            # バイナリを変更
            modified_binary = modify_fill_color_in_binary(
                original_binary,
                old_r, old_g, old_b,
                new_r, new_g, new_b
            )

            # base64エンコード
            new_b64 = base64.b64encode(modified_binary).decode('ascii')

            # 変更を記録
            modifications.append({
                'match': match,
                'new_b64': new_b64,
                'style_name': prsl_style.name
            })

            print(f"    ✓ 変換成功 ({len(original_binary)} → {len(modified_binary)} bytes)")

        except Exception as e:
            print(f"    ✗ エラー: {e}")
            modifications.append(None)

    # ファイル内容を更新
    print(f"\n[5] ファイル更新:")
    new_content = content

    # 後ろから順に置換（オフセットが変わらないように）
    for i in range(len(modifications) - 1, -1, -1):
        if modifications[i] is not None:
            mod = modifications[i]
            match = mod['match']
            new_b64 = mod['new_b64']

            # base64部分を置換
            new_content = (
                new_content[:match.start(2)] +
                new_b64 +
                new_content[match.end(2):]
            )

    # スタイル名も更新（オプション）
    # Name要素を順番に置換
    name_pattern = r'<Name>(\d+)</Name>'
    name_matches = list(re.finditer(name_pattern, new_content))

    for i, mod in enumerate(modifications):
        if mod is not None and i < len(name_matches):
            name_match = name_matches[i]
            style_name = mod['style_name']
            # 改行とタブを除去してシンプルに
            simple_name = style_name.replace('\n', ' ').replace('\t', ' ').strip()
            new_content = (
                new_content[:name_match.start(1)] +
                simple_name[:50] +  # 最大50文字
                new_content[name_match.end(1):]
            )

    # ファイルに保存
    print(f"\n[6] ファイル保存: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  ✓ {len(new_content)} 文字を書き込み")

    print(f"\n{'='*80}")
    print("✓✓✓ 変換完了！")
    print('='*80)
    print(f"\n出力ファイル: {output_path}")
    print(f"変換スタイル数: {len([m for m in modifications if m is not None])}/{len(prsl_styles)}")
    print(f"\nPremiere Proで {output_path} を読み込んでテストしてください！")

def main():
    """メイン関数"""

    # デフォルトパス
    prsl_path = "/tmp/10styles.prsl"
    template_path = "/tmp/10styles.prtextstyle"
    output_path = "/home/user/telop01/converted_styles.prtextstyle"

    # コマンドライン引数がある場合は使用
    if len(sys.argv) > 1:
        prsl_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    if len(sys.argv) > 3:
        template_path = sys.argv[3]

    # 変換実行
    convert_prsl_to_prtextstyle(prsl_path, template_path, output_path)

if __name__ == "__main__":
    main()
