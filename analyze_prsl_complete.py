#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRSL Stylelist 形式の完全解析ツール
全ての要素、属性、データ型を文書化
"""

from xml.etree import ElementTree as ET
from collections import defaultdict
import sys

def analyze_prsl_complete(filepath: str):
    """PRSL形式を完全解析"""

    tree = ET.parse(filepath)
    root = tree.getroot()

    # 統計情報
    tag_counts = defaultdict(int)
    tag_attributes = defaultdict(set)
    tag_text_samples = defaultdict(list)
    tag_children = defaultdict(set)
    tag_parents = defaultdict(set)

    # 全要素を走査
    def traverse(elem, parent_tag=None):
        tag = elem.tag
        tag_counts[tag] += 1

        # 属性
        for attr in elem.attrib:
            tag_attributes[tag].add(attr)

        # テキスト（サンプル）
        if elem.text and elem.text.strip():
            text = elem.text.strip()
            if len(tag_text_samples[tag]) < 3:  # 最大3サンプル
                tag_text_samples[tag].append(text)

        # 親子関係
        if parent_tag:
            tag_parents[tag].add(parent_tag)

        # 子要素
        for child in elem:
            tag_children[tag].add(child.tag)
            traverse(child, tag)

    traverse(root)

    print("=" * 80)
    print(f"PRSL Stylelist 形式完全解析: {filepath}")
    print("=" * 80)

    print(f"\nルート要素: <{root.tag}>")
    if root.attrib:
        print(f"ルート属性: {dict(root.attrib)}")

    print(f"\n総タグ種類数: {len(tag_counts)}")
    print(f"総要素数: {sum(tag_counts.values())}")

    # タグ一覧（アルファベット順）
    print("\n" + "=" * 80)
    print("全タグ詳細（アルファベット順）")
    print("=" * 80)

    for tag in sorted(tag_counts.keys()):
        print(f"\n<{tag}>")
        print(f"  出現回数: {tag_counts[tag]}")

        if tag_attributes[tag]:
            print(f"  属性: {sorted(tag_attributes[tag])}")

        if tag_children[tag]:
            print(f"  子要素: {sorted(tag_children[tag])}")

        if tag_parents[tag]:
            print(f"  親要素: {sorted(tag_parents[tag])}")

        if tag_text_samples[tag]:
            print(f"  テキストサンプル:")
            for sample in tag_text_samples[tag]:
                if len(sample) > 60:
                    sample = sample[:60] + "..."
                print(f"    - {repr(sample)}")

    # 構造ツリー（最初のstyleblockのみ）
    print("\n" + "=" * 80)
    print("構造ツリー（最初のstyleblock）")
    print("=" * 80)

    styleblock = root.find('styleblock')
    if styleblock:
        print_tree(styleblock, indent=0, max_depth=5)

    return {
        'tag_counts': dict(tag_counts),
        'tag_attributes': {k: list(v) for k, v in tag_attributes.items()},
        'tag_children': {k: list(v) for k, v in tag_children.items()},
        'tag_parents': {k: list(v) for k, v in tag_parents.items()},
    }

def print_tree(elem, indent=0, max_depth=10):
    """要素ツリーを表示"""
    if indent > max_depth:
        return

    prefix = "  " * indent

    # タグ名と属性
    attrs = " ".join(f'{k}="{v}"' for k, v in elem.attrib.items())
    if attrs:
        tag_str = f"<{elem.tag} {attrs}>"
    else:
        tag_str = f"<{elem.tag}>"

    # テキスト
    if elem.text and elem.text.strip():
        text = elem.text.strip()
        if len(text) > 40:
            text = text[:40] + "..."
        print(f"{prefix}{tag_str} = {repr(text)}")
    else:
        print(f"{prefix}{tag_str}")
        for child in elem:
            print_tree(child, indent + 1, max_depth)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        prsl_file = "10styles.prsl"
    else:
        prsl_file = sys.argv[1]

    stats = analyze_prsl_complete(prsl_file)

    # 統計をJSON形式で保存
    import json
    with open("prsl_analysis_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("✅ 解析完了")
    print("=" * 80)
    print("統計データを prsl_analysis_stats.json に保存しました")
