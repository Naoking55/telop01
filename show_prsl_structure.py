#!/usr/bin/env python3
"""
PRSLファイルの完全構造を表示
"""

import xml.etree.ElementTree as ET

prsl_path = '/home/user/telop01/10styles/10styles.prsl'

tree = ET.parse(prsl_path)
root = tree.getroot()

# 最初のスタイルの完全な構造を表示
styleblock = root.find('.//styleblock')

if styleblock:
    print("="*80)
    print("最初のスタイルブロックの完全構造")
    print("="*80)

    def print_element(elem, indent=0):
        """要素を再帰的に表示"""
        prefix = "  " * indent

        # タグ名と属性
        attrs = " ".join(f'{k}="{v}"' for k, v in elem.attrib.items())
        if attrs:
            print(f"{prefix}<{elem.tag} {attrs}>", end="")
        else:
            print(f"{prefix}<{elem.tag}>", end="")

        # テキスト
        if elem.text and elem.text.strip():
            text = elem.text.strip()
            if len(text) > 50:
                text = text[:50] + "..."
            print(f" {text}", end="")

        # 子要素があるか
        if len(elem) > 0:
            print()
            for child in elem:
                print_element(child, indent + 1)
            print(f"{prefix}</{elem.tag}>")
        else:
            if elem.tail and elem.tail.strip():
                print(f"</{elem.tag}> {elem.tail.strip()[:30]}")
            else:
                print(f"</{elem.tag}>")

    print_element(styleblock)

# style_data内の全要素名をリスト
print("\n" + "="*80)
print("style_data内の全要素名")
print("="*80)

style_data = root.find('.//style_data')
if style_data:
    for child in style_data:
        print(f"- {child.tag}")
        if len(child) > 0:
            for subchild in child:
                print(f"  - {subchild.tag}")
