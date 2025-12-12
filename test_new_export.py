#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新しいエクスポート形式のテスト（float色対応）
"""

import sys
import os
sys.path.insert(0, '/home/user/telop01')

print("=" * 70)
print("Premiere Pro 2025 対応エクスポートテスト")
print("=" * 70)

# PRSLからスタイルを読み込み
from prsl_parser_stylelist import parse_prsl_stylelist

test_file = "10styles.prsl"
styles = parse_prsl_stylelist(test_file)
print(f"\n✓ {len(styles)} スタイルを読み込み")

if not styles:
    sys.exit(1)

# 最初のスタイル
style = styles[0]
print(f"\nスタイル: {style.name}")
print(f"  フォント: {style.font_family} ({style.font_size}pt)")
print(f"  塗り色: RGB({style.fill.r}, {style.fill.g}, {style.fill.b}, {style.fill.a})")

# エクスポート（新形式: float色）
print("\n" + "=" * 70)
print("エクスポート（Premiere 2025 float形式）")
print("=" * 70)

# モジュールを再ロード
import importlib
import prsl_converter_modern
importlib.reload(prsl_converter_modern)

from prsl_converter_modern import export_prtextstyle

output_file = "test_premiere2025.prtextstyle"
export_prtextstyle(style, output_file)

print(f"\n✓ エクスポート完了: {output_file}")
print(f"  ファイルサイズ: {os.path.getsize(output_file)} bytes")

# 解析
print("\n" + "=" * 70)
print("バイナリ解析")
print("=" * 70)

import subprocess
subprocess.run(["python3", "analyze_prtextstyle.py", output_file])

print("\n" + "=" * 70)
print("✅ テスト完了")
print("=" * 70)
print(f"\n生成されたファイル: {output_file}")
print("このファイルを Premiere Pro 2025 でインポートしてテストしてください。")
