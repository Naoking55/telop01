#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エクスポート形式テスト
実際にprtextstyleを書き出して内容を確認
"""

import sys
sys.path.insert(0, '/home/user/telop01')

print("=" * 70)
print("prtextstyle エクスポート形式テスト")
print("=" * 70)

# PRSLファイルを読み込み
print("\n[1] PRSLファイルを読み込み...")
from prsl_parser_stylelist import parse_prsl_stylelist

test_file = "10styles.prsl"
styles = parse_prsl_stylelist(test_file)
print(f"✓ {len(styles)} スタイルを読み込み")

if not styles:
    print("✗ スタイルが見つかりません")
    sys.exit(1)

# 最初のスタイルを使用
style = styles[0]
print(f"\nテスト対象: {style.name}")
print(f"  フォント: {style.font_family}")
print(f"  サイズ: {style.font_size}pt")
print(f"  塗り: {style.fill.fill_type}")
if style.fill.fill_type == "solid":
    print(f"  色: RGB({style.fill.r}, {style.fill.g}, {style.fill.b}, {style.fill.a})")
print(f"  シャドウ: {style.shadow.enabled}")

# エクスポート
print("\n[2] prtextstyle 形式でエクスポート...")
from prsl_test_simple import export_prtextstyle

output_file = "test_export_format.prtextstyle"
try:
    export_prtextstyle(style, output_file)
    print(f"✓ エクスポート完了: {output_file}")

    # ファイルサイズ確認
    import os
    size = os.path.getsize(output_file)
    print(f"  ファイルサイズ: {size} bytes")

    # 内容をプレビュー
    print("\n[3] XMLプレビュー:")
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        for i, line in enumerate(lines[:15], 1):
            print(f"  {i:2d}: {line}")
        if len(lines) > 15:
            print(f"  ... ({len(lines)} 行)")

    # バイナリ解析を実行
    print("\n" + "=" * 70)
    print("[4] バイナリ内容を解析...")
    print("=" * 70)
    import subprocess
    subprocess.run(["python3", "analyze_prtextstyle.py", output_file])

except Exception as e:
    print(f"✗ エラー: {e}")
    import traceback
    traceback.print_exc()
