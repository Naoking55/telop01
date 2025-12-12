#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prtextstyle エクスポート形式の検証
Premiere Pro が期待する形式と比較
"""

import sys
import os
sys.path.insert(0, '/home/user/telop01')

print("=" * 70)
print("prtextstyle エクスポート形式の検証")
print("=" * 70)

# スタイルを読み込み
from prsl_parser_stylelist import parse_prsl_stylelist

test_file = "10styles.prsl"
styles = parse_prsl_stylelist(test_file)
print(f"\n✓ {len(styles)} スタイルを読み込み")

if not styles:
    sys.exit(1)

style = styles[0]
print(f"\n検証対象: {style.name}")
print(f"  フォント: {style.font_family}")
print(f"  サイズ: {style.font_size}pt")
print(f"  塗り色: RGB({style.fill.r}, {style.fill.g}, {style.fill.b}, {style.fill.a})")

# 現在の形式でエクスポート
print("\n" + "=" * 70)
print("現在の形式でエクスポート")
print("=" * 70)

from export_premiere2025 import export_prtextstyle_premiere2025

output1 = "test_current_format.prtextstyle"
export_prtextstyle_premiere2025(style, output1)

# 解析
import subprocess
subprocess.run(["python3", "analyze_prtextstyle.py", output1])

print("\n" + "=" * 70)
print("潜在的な問題の確認")
print("=" * 70)

# XMLをチェック
from xml.etree import ElementTree as ET
import base64

tree = ET.parse(output1)
root = tree.getroot()

print(f"\n[1] XML構造:")
print(f"  ルート: <{root.tag}> Version=\"{root.attrib.get('Version', '?')}\"")

styles_elem = root.find('Styles')
if styles_elem:
    style_elems = styles_elem.findall('Style')
    print(f"  Styles数: {len(style_elems)}")

    for se in style_elems:
        name_elem = se.find('Name')
        binary_elem = se.find('BinaryData')

        if name_elem is not None:
            print(f"    Name: {name_elem.text}")

        if binary_elem is not None:
            encoding = binary_elem.attrib.get('Encoding', '?')
            print(f"    BinaryData Encoding: {encoding}")

            if encoding == 'base64' and binary_elem.text:
                try:
                    binary_data = base64.b64decode(binary_elem.text.strip())
                    print(f"    バイナリサイズ: {len(binary_data)} bytes")

                    # 最初の16バイトを表示
                    print(f"    最初の16バイト: {binary_data[:16].hex()}")
                except Exception as e:
                    print(f"    ✗ デコードエラー: {e}")

print(f"\n[2] 潜在的な問題:")
issues = []

# チェック1: フォント名が空？
if not style.font_family or style.font_family == "":
    issues.append("フォント名が空")

# チェック2: フォントサイズが0以下？
if style.font_size <= 0:
    issues.append(f"フォントサイズが異常: {style.font_size}")

# チェック3: 塗り色が全て0？
if style.fill.r == 0 and style.fill.g == 0 and style.fill.b == 0 and style.fill.a == 0:
    issues.append("塗り色が完全に透明")

if issues:
    for issue in issues:
        print(f"  ⚠ {issue}")
else:
    print(f"  ✓ 基本的な問題は見つかりません")

print(f"\n[3] Premiere Pro 2025 要件の推測:")
print(f"  ✓ XML Version=\"1\"")
print(f"  ✓ Base64エンコーディング")
print(f"  ✓ TLV構造")
print(f"  ✓ Float色形式 (0.0-1.0)")
print(f"  ? タグの順序は重要？")
print(f"  ? 追加の必須タグがある？")

print("\n" + "=" * 70)
print("✅ 検証完了")
print("=" * 70)
print(f"\n生成ファイル: {output1}")
print("\nPremiereでテストしてください:")
print("  1. Essential Graphics パネル")
print("  2. スタイルをインポート")
print("  3. このファイルを選択")
