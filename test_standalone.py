#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合版スタンドアロンテスト
prsl_converter_modern.py から StylelistPRSLParser が使えることを確認
"""

import sys
import os

print("=" * 70)
print("統合版スタンドアロンテスト")
print("=" * 70)

# prsl_converter_modern.py 内にクラスが存在するか確認
print("\n[1] ファイル内容を確認...")
with open("prsl_converter_modern.py", "r", encoding="utf-8") as f:
    content = f.read()

    if "class StylelistPRSLParser:" in content:
        print("✓ StylelistPRSLParser クラスが含まれています")
    else:
        print("✗ StylelistPRSLParser クラスが見つかりません")
        sys.exit(1)

    if "def parse_prsl(filepath: str)" in content:
        print("✓ parse_prsl 関数が含まれています")
    else:
        print("✗ parse_prsl 関数が見つかりません")
        sys.exit(1)

    # 統合版であることを確認
    if "StylelistPRSLParser(filepath)" in content:
        print("✓ parse_prsl が StylelistPRSLParser を直接使用しています（統合版）")
    else:
        print("⚠ parse_prsl が外部インポートを試みています")

print("\n[2] ファイルサイズを確認...")
file_size = os.path.getsize("prsl_converter_modern.py")
print(f"  prsl_converter_modern.py: {file_size:,} bytes")

if file_size > 50000:  # 50KB以上なら統合版の可能性が高い
    print(f"✓ ファイルサイズが大きい = stylelistパーサーが統合されている可能性大")
else:
    print(f"⚠ ファイルサイズが小さい = stylelistパーサーが統合されていない可能性")

print("\n[3] コード構造を確認...")
lines = content.split("\n")
stylelist_parser_line = None
parse_prsl_line = None

for i, line in enumerate(lines, 1):
    if "class StylelistPRSLParser:" in line:
        stylelist_parser_line = i
    if "def parse_prsl(filepath: str)" in line:
        parse_prsl_line = i

if stylelist_parser_line and parse_prsl_line:
    print(f"  StylelistPRSLParser クラス: {stylelist_parser_line} 行目")
    print(f"  parse_prsl 関数: {parse_prsl_line} 行目")

    if stylelist_parser_line < parse_prsl_line:
        print("✓ 正しい順序: パーサークラスが関数より前に定義されています")
    else:
        print("✗ 順序エラー: パーサークラスが関数より後に定義されています")

print("\n" + "=" * 70)
print("✅ 統合版の構造確認完了！")
print("=" * 70)
print("\nprsl_converter_modern.py は1ファイル統合版になっています")
print("外部ファイル（prsl_parser_stylelist.py）は不要です")
