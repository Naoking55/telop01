#!/usr/bin/env python3
"""
Fill色変更のテスト
手動変換したprtextstyleファイルのFill色を変更して、パターンが正しいか検証
"""

import sys
import xml.etree.ElementTree as ET
import base64
sys.path.insert(0, '/home/user/telop01')

from prtextstyle_editor import PrtextstyleEditor

MARKER = b'\x02\x00\x00\x00\x41\x61'

def find_marker_position(binary):
    """マーカーの位置を探す"""
    try:
        return binary.index(MARKER)
    except ValueError:
        return -1

def modify_fill_color(binary, old_r, old_g, old_b, new_r, new_g, new_b):
    """
    Fill色を変更する

    ルール：
    - マーカーの直前に、255以外のRGB成分を順番に格納
    - R, G, Bの順で、255の成分は省略、それ以外（0を含む）は格納
    """
    binary = bytearray(binary)

    # マーカーを見つける
    marker_pos = find_marker_position(binary)
    if marker_pos == -1:
        raise ValueError("Marker not found in binary")

    print(f"Marker found at: 0x{marker_pos:04x}")

    # 古い色バイト列を計算
    old_color_bytes = []
    if old_r != 255:
        old_color_bytes.append(old_r)
    if old_g != 255:
        old_color_bytes.append(old_g)
    if old_b != 255:
        old_color_bytes.append(old_b)

    # 新しいFill色バイト列を作成
    new_color_bytes = []
    if new_r != 255:
        new_color_bytes.append(new_r)
    if new_g != 255:
        new_color_bytes.append(new_g)
    if new_b != 255:
        new_color_bytes.append(new_b)

    print(f"Old color: RGB({old_r}, {old_g}, {old_b}) -> bytes: {old_color_bytes}")
    print(f"New color: RGB({new_r}, {new_g}, {new_b}) -> bytes: {new_color_bytes}")

    old_color_length = len(old_color_bytes)
    new_color_length = len(new_color_bytes)

    # マーカー直前のバイトを確認
    if old_color_length > 0:
        actual_old_bytes = list(binary[marker_pos - old_color_length:marker_pos])
        print(f"Actual bytes before marker: {actual_old_bytes}")
        if actual_old_bytes == old_color_bytes:
            print("✓ Old color bytes match expected!")
        else:
            print("✗ WARNING: Old color bytes don't match!")

    if old_color_length == new_color_length:
        # 同じ長さなら単純に置き換え
        for i, byte_val in enumerate(new_color_bytes):
            binary[marker_pos - new_color_length + i] = byte_val
        print("✓ Color bytes replaced (same length)")
    else:
        print(f"✗ Different color byte length: {old_color_length} -> {new_color_length}")
        print("  This requires inserting/deleting bytes and updating FlatBuffers offsets")
        print("  Attempting simple insert/delete (may break the file)...")

        # 古い色バイトを削除
        del binary[marker_pos - old_color_length:marker_pos]

        # 新しいマーカー位置
        new_marker_pos = marker_pos - old_color_length

        # 新しい色バイトを挿入
        for i, byte_val in enumerate(new_color_bytes):
            binary.insert(new_marker_pos + i, byte_val)

        print("✓ Bytes modified (WARNING: FlatBuffers offsets may be broken!)")

    return bytes(binary)

def create_test_file():
    """
    テストファイルを作成
    Style 1 (RGB(0, 114, 255)) を RGB(100, 200, 50) に変更
    """

    print("="*80)
    print("Fill色変更テスト")
    print("="*80)

    # 手動変換prtextstyleを読み込み
    editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")

    # Style 1を取得
    style_name = list(editor.styles.keys())[0]
    original_binary = editor.get_style_binary(style_name)

    print(f"\nOriginal style: {style_name}")
    print(f"Original binary size: {len(original_binary)} bytes")

    # Style 1の元の色
    old_r, old_g, old_b = 0, 114, 255
    print(f"Original fill color: RGB({old_r}, {old_g}, {old_b})")

    # Fill色を変更（同じバイト数で テスト：2バイト -> 2バイト）
    new_r, new_g, new_b = 100, 200, 255
    modified_binary = modify_fill_color(original_binary, old_r, old_g, old_b, new_r, new_g, new_b)

    print(f"\nModified binary size: {len(modified_binary)} bytes")

    # 新しいprtextstyleファイルを作成
    output_path = "/home/user/telop01/test_fill_color_RGB_100_200_50.prtextstyle"

    # XMLを作成
    root = ET.Element('TextStyles')
    root.set('Version', '1')

    # スタイルを追加
    style = ET.SubElement(root, 'TextStyle')

    name = ET.SubElement(style, 'Name')
    name.text = f"TEST - Fill RGB({new_r}, {new_g}, {new_b})"

    data = ET.SubElement(style, 'Data')
    data.text = base64.b64encode(modified_binary).decode('ascii')

    # ファイルに保存
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding='utf-8', xml_declaration=True)

    print(f"\n✓ Test file created: {output_path}")
    print(f"\nPlease test this file in Premiere Pro!")
    print(f"Expected fill color: RGB({new_r}, {new_g}, {new_b})")

    return output_path

if __name__ == "__main__":
    create_test_file()
