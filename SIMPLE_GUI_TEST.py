#!/usr/bin/env python3
"""
GUI v2.1のロジックを簡易テスト
（tkinter不要版）
"""

import sys
import re
import base64
import os

sys.path.insert(0, '/home/user/telop01')

# PRSLパーサーをインポート
from test_prsl_conversion import parse_prsl

# マーカー定義
MARKER = b'\x02\x00\x00\x00\x41\x61'

def get_color_structure(r, g, b):
    """色構造を取得"""
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

def replace_color_bytes_in_binary(binary, target_r, target_g, target_b):
    """バイナリ内の色バイトを置換"""
    binary = bytearray(binary)

    marker_pos = binary.find(MARKER)
    if marker_pos == -1:
        print(f"    ⚠️ マーカーが見つかりません")
        return bytes(binary)

    target_structure, new_components = get_color_structure(target_r, target_g, target_b)
    num_bytes = len(new_components)

    for i in range(num_bytes):
        _, value = new_components[i]
        binary[marker_pos - num_bytes + i] = value

    return bytes(binary)

def batch_export_cli_style(styles, output_path, template_path):
    """GUI v2.1の _batch_export_cli_style と同じロジック"""

    print(f"\n{'='*60}")
    print(f"バッチエクスポート開始")
    print(f"{'='*60}")
    print(f"出力: {output_path}")
    print(f"テンプレート: {template_path}")
    print(f"スタイル数: {len(styles)}")

    # テンプレートファイル全体を読み込み
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    print(f"テンプレートサイズ: {len(template_content)} chars ({len(template_content)/1024:.1f} KB)")

    # StartKeyframeValue エントリを抽出
    pattern = r'(<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">)([A-Za-z0-9+/=\s]+)(</StartKeyframeValue>)'
    matches = list(re.finditer(pattern, template_content, re.DOTALL))

    print(f"StartKeyframeValue エントリ: {len(matches)}個")

    if len(matches) < len(styles):
        raise ValueError(f"テンプレートのスタイル数({len(matches)})が不足しています。{len(styles)}個必要です。")

    # テンプレートのバイナリを取得
    template_binaries = []
    for i, match in enumerate(matches):
        b64 = match.group(2).replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
        binary = base64.b64decode(b64)
        template_binaries.append(binary)

    print(f"\n変換処理:")

    # 各スタイルを変換
    conversions = []
    success_count = 0

    for i, style in enumerate(styles):
        r, g, b = style.fill.r, style.fill.g, style.fill.b

        print(f"  {i+1}/{len(styles)}: {style.name} - RGB({r}, {g}, {b})")

        target_structure, new_stored = get_color_structure(r, g, b)

        if i < len(template_binaries):
            template_binary = template_binaries[i]

            try:
                modified_binary = replace_color_bytes_in_binary(template_binary, r, g, b)
                new_b64 = base64.b64encode(modified_binary).decode('ascii')

                conversions.append(new_b64)
                success_count += 1
                print(f"    ✓ 変換成功")

            except Exception as e:
                print(f"    ✗ エラー: {e}")
                conversions.append(None)
        else:
            conversions.append(None)

    print(f"\n変換完了: {success_count}/{len(styles)}")

    # ファイル更新（後ろから順に置換）
    new_content = template_content
    for i in range(len(conversions) - 1, -1, -1):
        if conversions[i] is not None and i < len(matches):
            match = matches[i]
            new_b64 = conversions[i]

            new_content = (
                new_content[:match.start(2)] +
                new_b64 +
                new_content[match.end(2):]
            )

    print(f"新コンテンツサイズ: {len(new_content)} chars ({len(new_content)/1024:.1f} KB)")

    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    final_size = os.path.getsize(output_path)
    print(f"\n✓ ファイル保存完了: {output_path}")
    print(f"✓ ファイルサイズ: {final_size} bytes ({final_size/1024:.1f} KB)")

    if final_size < 10000:
        print(f"⚠️⚠️⚠️ ファイルサイズが異常に小さい！")
    else:
        print(f"✓ ファイルサイズ正常")

    return success_count

# メイン処理
if __name__ == "__main__":
    print("="*60)
    print("GUI v2.1 ロジック簡易テスト")
    print("="*60)

    prsl_file = "/tmp/10styles.prsl"
    template_file = "/tmp/10styles.prtextstyle"
    output_file = "/home/user/telop01/SIMPLE_GUI_TEST_output.prtextstyle"

    # PRSLを解析
    print(f"\nPRSL解析: {prsl_file}")
    styles = parse_prsl(prsl_file)
    print(f"  ✓ {len(styles)} スタイルを検出")

    # バッチエクスポート実行
    success_count = batch_export_cli_style(styles, output_file, template_file)

    print(f"\n{'='*60}")
    print(f"テスト完了")
    print(f"{'='*60}")
    print(f"\n結果: {output_file}")
    print(f"成功: {success_count}/{len(styles)} スタイル")
