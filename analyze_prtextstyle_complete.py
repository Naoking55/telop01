#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prtextstyle 形式の完全解析ツール
Premiere Pro 2025 の実際のフォーマットを文書化
"""

from xml.etree import ElementTree as ET
from collections import defaultdict
import base64
import sys

def analyze_prtextstyle_complete(filepath: str):
    """prtextstyle形式を完全解析"""

    tree = ET.parse(filepath)
    root = tree.getroot()

    # 統計情報
    tag_counts = defaultdict(int)
    tag_attributes = defaultdict(set)
    classid_map = {}  # ClassID -> タグ名のマップ
    objectref_map = defaultdict(list)  # ObjectRef -> 参照元のマップ

    # 全要素を走査
    def traverse(elem):
        tag = elem.tag
        tag_counts[tag] += 1

        # 属性
        for attr in elem.attrib:
            tag_attributes[tag].add(attr)

        # ClassID を記録
        if 'ClassID' in elem.attrib:
            classid_map[elem.attrib['ClassID']] = tag

        # ObjectRef を記録
        if 'ObjectRef' in elem.attrib:
            objectref_map[elem.attrib['ObjectRef']].append(tag)

        # 子要素
        for child in elem:
            traverse(child)

    traverse(root)

    print("=" * 80)
    print(f"prtextstyle 形式完全解析: {filepath}")
    print("=" * 80)

    print(f"\nルート要素: <{root.tag}>")
    if root.attrib:
        print(f"ルート属性: {dict(root.attrib)}")

    print(f"\n総タグ種類数: {len(tag_counts)}")
    print(f"総要素数: {sum(tag_counts.values())}")

    # 重要な要素の検索
    print("\n" + "=" * 80)
    print("重要な要素")
    print("=" * 80)

    # StyleProjectItem
    style_items = root.findall(".//StyleProjectItem")
    print(f"\nStyleProjectItem: {len(style_items)} 個")
    for i, item in enumerate(style_items, 1):
        name = item.find(".//Name")
        name_text = name.text if name is not None and name.text else "?"
        print(f"  {i}. {name_text}")
        print(f"     ObjectUID: {item.attrib.get('ObjectUID', '?')}")
        print(f"     ClassID: {item.attrib.get('ClassID', '?')}")

    # VideoFilterComponent (テキストコンポーネント)
    video_filters = root.findall(".//VideoFilterComponent")
    text_components = [vf for vf in video_filters if vf.find(".//MatchName") is not None
                       and vf.find(".//MatchName").text == "AE.ADBE Text"]
    print(f"\nVideoFilterComponent (AE.ADBE Text): {len(text_components)} 個")
    for i, comp in enumerate(text_components, 1):
        print(f"  {i}. ObjectID: {comp.attrib.get('ObjectID', '?')}")

    # ArbVideoComponentParam (バイナリデータ)
    arb_params = root.findall(".//ArbVideoComponentParam")
    print(f"\nArbVideoComponentParam: {len(arb_params)} 個")
    for i, param in enumerate(arb_params[:3], 1):  # 最初の3つ
        name = param.find("Name")
        name_text = name.text if name is not None and name.text else "?"
        print(f"  {i}. {name_text}")
        print(f"     ObjectID: {param.attrib.get('ObjectID', '?')}")

        # バイナリデータサイズ
        keyframe_val = param.find("StartKeyframeValue")
        if keyframe_val is not None and keyframe_val.text:
            encoding = keyframe_val.attrib.get('Encoding', '?')
            if encoding == 'base64':
                try:
                    binary = base64.b64decode(keyframe_val.text.strip())
                    print(f"     バイナリサイズ: {len(binary)} bytes")
                    print(f"     最初の32バイト: {binary[:32].hex()}")
                except:
                    pass

    # ClassID 一覧
    print("\n" + "=" * 80)
    print("ClassID 一覧")
    print("=" * 80)
    for classid in sorted(classid_map.keys()):
        print(f"{classid}: <{classid_map[classid]}>")

    # タグ統計
    print("\n" + "=" * 80)
    print("タグ出現回数（上位20）")
    print("=" * 80)
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    for tag, count in sorted_tags[:20]:
        attrs = sorted(tag_attributes[tag])
        print(f"<{tag}>: {count} 回")
        if attrs:
            print(f"  属性: {attrs}")

    # 構造の階層
    print("\n" + "=" * 80)
    print("XML構造の概要")
    print("=" * 80)
    print_structure_tree(root, max_depth=3)

    return {
        'tag_counts': dict(tag_counts),
        'classid_map': classid_map,
        'style_count': len(style_items),
    }

def print_structure_tree(elem, indent=0, max_depth=3, shown_children=3):
    """構造ツリーを表示（簡略版）"""
    if indent > max_depth:
        return

    prefix = "  " * indent

    # タグと属性
    attrs_str = ""
    if 'ObjectID' in elem.attrib:
        attrs_str = f" ObjectID={elem.attrib['ObjectID']}"
    elif 'ObjectUID' in elem.attrib:
        attrs_str = f" ObjectUID={elem.attrib['ObjectUID'][:8]}..."
    elif 'ClassID' in elem.attrib:
        attrs_str = f" ClassID={elem.attrib['ClassID'][:20]}..."

    # 子要素の数
    children = list(elem)
    child_count = len(children)

    if child_count == 0:
        # テキストがあれば表示
        if elem.text and elem.text.strip():
            text = elem.text.strip()
            if len(text) > 30:
                text = text[:30] + "..."
            print(f"{prefix}<{elem.tag}{attrs_str}> = {repr(text)}")
        else:
            print(f"{prefix}<{elem.tag}{attrs_str}/>")
    else:
        print(f"{prefix}<{elem.tag}{attrs_str}> ({child_count} children)")
        # 最初の数個の子要素のみ表示
        for child in children[:shown_children]:
            print_structure_tree(child, indent + 1, max_depth, shown_children)
        if child_count > shown_children:
            print(f"{'  ' * (indent + 1)}... and {child_count - shown_children} more")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        prtextstyle_file = "TEMPLATE_SolidFill_White.prtextstyle"
    else:
        prtextstyle_file = sys.argv[1]

    stats = analyze_prtextstyle_complete(prtextstyle_file)

    # 統計をJSON形式で保存
    import json
    with open("prtextstyle_analysis_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("✅ 解析完了")
    print("=" * 80)
    print("統計データを prtextstyle_analysis_stats.json に保存しました")
