#!/usr/bin/env python3
"""
成功している手動変換ファイルを使ったテスト
Style 2 (RGB(255, 0, 126)) → Style 4 (RGB(255, 174, 0)) に変換
これらは同じサイズ(416バイト)で、色バイトだけ2バイト異なることが確認済み
"""

import sys
import xml.etree.ElementTree as ET
import base64
sys.path.insert(0, '/home/user/telop01')

from prtextstyle_editor import PrtextstyleEditor

MARKER = b'\x02\x00\x00\x00\x41\x61'

def create_test_from_known_good():
    """
    Style 2をベースにして、Style 4の色に変換
    """

    print("="*80)
    print("Known Good Conversion Test")
    print("Style 2 (416 bytes) → Style 4 color")
    print("="*80)

    # 手動変換prtextstyleを読み込み
    editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")

    # Style 2を取得 (RGB(255, 0, 126))
    style2_binary = editor.get_style_binary(list(editor.styles.keys())[1])
    print(f"\nStyle 2 (base):")
    print(f"  Color: RGB(255, 0, 126)")
    print(f"  Binary size: {len(style2_binary)} bytes")

    # マーカー位置
    marker_pos = style2_binary.index(MARKER)
    print(f"  Marker at: 0x{marker_pos:04x}")

    # 色バイト
    color_bytes = style2_binary[marker_pos-2:marker_pos]
    print(f"  Color bytes: {list(color_bytes)} (should be [0, 126])")

    # Style 4の色にコピー (RGB(255, 174, 0))
    # 期待される色バイト: [174, 0]
    new_binary = bytearray(style2_binary)
    new_binary[marker_pos-2] = 174
    new_binary[marker_pos-1] = 0

    print(f"\nModified to Style 4 color:")
    print(f"  Target color: RGB(255, 174, 0)")
    print(f"  New color bytes: [174, 0]")

    # 検証
    new_marker_pos = new_binary.index(MARKER)
    new_color_bytes = new_binary[new_marker_pos-2:new_marker_pos]
    print(f"  Verified color bytes: {list(new_color_bytes)}")

    # Style 4の実際のバイナリと比較
    style4_binary = editor.get_style_binary(list(editor.styles.keys())[3])
    print(f"\nComparison with actual Style 4:")
    print(f"  Style 4 size: {len(style4_binary)} bytes")

    if len(new_binary) == len(style4_binary):
        diffs = [i for i in range(len(new_binary)) if new_binary[i] != style4_binary[i]]
        print(f"  Differences: {len(diffs)} bytes")
        if len(diffs) <= 10:
            for d in diffs:
                print(f"    0x{d:04x}: created={new_binary[d]}, actual={style4_binary[d]}")

        if len(diffs) == 0:
            print(f"  ✓✓✓ PERFECT MATCH with Style 4!")
    else:
        print(f"  ✗ Size mismatch")

    # 新しいprtextstyleファイルを作成
    output_path = "/home/user/telop01/test_style2_to_style4.prtextstyle"

    # XMLを作成
    root = ET.Element('TextStyles')
    root.set('Version', '1')

    # スタイルを追加
    style = ET.SubElement(root, 'TextStyle')

    name = ET.SubElement(style, 'Name')
    name.text = f"TEST - Style2→Style4 - RGB(255, 174, 0)"

    data = ET.SubElement(style, 'Data')
    data.text = base64.b64encode(bytes(new_binary)).decode('ascii')

    # ファイルに保存
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding='utf-8', xml_declaration=True)

    print(f"\n✓ Test file created: {output_path}")
    print(f"\nThis file should be IDENTICAL to Style 4!")
    print(f"Please test in Premiere Pro!")

if __name__ == "__main__":
    create_test_from_known_good()
