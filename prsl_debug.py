#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRSL ファイル構造デバッグツール

PRSLファイルの内部構造を詳しく表示します。
使い方: python prsl_debug.py <prslファイル>
"""

import sys
import base64
import struct
from xml.etree import ElementTree as ET

def decode_base64_floats(b64_text):
    """Base64をfloat配列にデコード"""
    if not b64_text:
        return []
    try:
        raw = base64.b64decode(b64_text)
        values = []
        for i in range(0, len(raw), 4):
            chunk = raw[i:i+4]
            if len(chunk) < 4:
                break
            value = struct.unpack("<f", chunk)[0]
            values.append(value)
        return values
    except Exception as e:
        return [f"ERROR: {e}"]

def analyze_prsl(filepath):
    """PRSLファイルを詳細に解析"""
    print("="*70)
    print(f"PRSL ファイル解析: {filepath}")
    print("="*70)

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        print(f"\nルート要素: {root.tag}")
        print(f"ルート属性: {root.attrib}")

        # 全体構造を表示
        print("\n--- XML 構造 ---")
        for i, elem in enumerate(root.iter(), 1):
            indent = "  " * len(list(elem.iterancestors()) if hasattr(elem, 'iterancestors') else [])
            attrs = f" {elem.attrib}" if elem.attrib else ""
            text_preview = f" = '{elem.text[:50]}...'" if elem.text and elem.text.strip() else ""
            print(f"{indent}<{elem.tag}>{attrs}{text_preview}")
            if i > 100:  # 最初の100要素のみ
                print("  ... (省略)")
                break

        # StyleProjectItem を検索
        print("\n--- StyleProjectItem 検索 ---")
        style_items = root.findall(".//StyleProjectItem")
        print(f"見つかった StyleProjectItem: {len(style_items)}個")

        if len(style_items) == 0:
            # 別のパターンを探す
            print("\n代替パターンを検索中...")

            # パターン1: Style
            styles = root.findall(".//Style")
            print(f"  <Style> 要素: {len(styles)}個")

            # パターン2: TextStyle
            text_styles = root.findall(".//TextStyle")
            print(f"  <TextStyle> 要素: {len(text_styles)}個")

            # パターン3: PremiereData配下
            premiere_data = root.findall(".//PremiereData")
            print(f"  <PremiereData> 要素: {len(premiere_data)}個")

            # 全タグ名を収集
            all_tags = set()
            for elem in root.iter():
                all_tags.add(elem.tag)

            print(f"\n使用されているタグ一覧 ({len(all_tags)}種類):")
            for tag in sorted(all_tags):
                count = len(root.findall(f".//{tag}"))
                print(f"  - {tag}: {count}個")

        else:
            # StyleProjectItem の詳細を表示
            for i, sp in enumerate(style_items[:3], 1):  # 最初の3つのみ
                print(f"\n--- StyleProjectItem #{i} ---")

                # Name
                name = sp.find(".//Name")
                if name is not None:
                    print(f"Name: {name.text}")

                # Param 要素
                params = sp.findall(".//Param")
                print(f"Param 数: {len(params)}個")

                for j, param in enumerate(params[:10], 1):  # 最初の10個
                    idx = param.attrib.get("Index", "?")
                    param_id = param.attrib.get("ParameterID", "?")

                    # StartKeyframeValue
                    val = param.find("StartKeyframeValue")
                    if val is not None and val.text:
                        b64 = val.text.strip()
                        floats = decode_base64_floats(b64)
                        print(f"  Param[{idx}] (ID:{param_id}): {floats[:5]}{'...' if len(floats) > 5 else ''}")

                if len(params) > 10:
                    print(f"  ... 他 {len(params)-10} 個の Param")

    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python prsl_debug.py <PRSLファイル>")
        sys.exit(1)

    analyze_prsl(sys.argv[1])
