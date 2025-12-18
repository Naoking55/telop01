#!/usr/bin/env python3
"""
正しいPremiereDataフォーマットでテストファイルを作成
手動変換ファイルをベースにして、1つのスタイルの色だけ変更
"""

import re
import base64
import sys

def modify_premiere_file():
    """
    手動変換ファイルの最初のスタイルの色を変更
    RGB(0, 114, 255) → RGB(100, 200, 255)
    """

    print("="*80)
    print("Creating test file in correct PremiereData format")
    print("="*80)

    # 手動変換ファイルを読み込み
    with open('/tmp/10styles.prtextstyle', 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"\nOriginal file size: {len(content)} characters")

    # 最初のStartKeyframeValueを探す（Style 1のバイナリ）
    # 改行を含む可能性があるので、DOTALLフラグを使用
    pattern = r'(<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">)([A-Za-z0-9+/=\s]+)(</StartKeyframeValue>)'

    matches = list(re.finditer(pattern, content, re.DOTALL))
    print(f"Found {len(matches)} StartKeyframeValue entries")

    if len(matches) < 1:
        print("✗ No StartKeyframeValue found!")
        return

    # 最初のスタイルのバイナリを変更
    first_match = matches[0]
    original_b64 = first_match.group(2)
    original_binary = base64.b64decode(original_b64)

    print(f"\nFirst style (Style 1):")
    print(f"  Original binary size: {len(original_binary)} bytes")

    # マーカーを探して色バイトを変更
    marker = b'\x02\x00\x00\x00\x41\x61'
    marker_pos = original_binary.find(marker)

    if marker_pos == -1:
        print("✗ Marker not found!")
        return

    print(f"  Marker at: 0x{marker_pos:04x}")

    # 元の色
    old_color = original_binary[marker_pos-2:marker_pos]
    print(f"  Original color bytes: {list(old_color)} (RGB(0, 114, 255))")

    # 新しい色に変更
    modified_binary = bytearray(original_binary)
    modified_binary[marker_pos-2] = 100  # R
    modified_binary[marker_pos-1] = 200  # G
    # B=255は省略されているのでそのまま

    print(f"  New color bytes: [100, 200] (RGB(100, 200, 255))")

    # base64エンコード
    new_b64 = base64.b64encode(bytes(modified_binary)).decode('ascii')

    print(f"  Modified binary size: {len(modified_binary)} bytes")
    print(f"  Size preserved: {len(original_binary) == len(modified_binary)}")

    # ファイル内容を置換
    new_content = content[:first_match.start(2)] + new_b64 + content[first_match.end(2):]

    print(f"\nModified file size: {len(new_content)} characters")

    # ファイル名も変更するために、最初のスタイル名を変更
    # Name が "001" の最初の出現を変更
    name_pattern = r'(<Name>)(001)(</Name>)'
    new_content = re.sub(name_pattern, r'\1TEST-RGB(100,200,255)\3', new_content, count=1)

    # 保存
    output_path = '/home/user/telop01/test_premiere_format.prtextstyle'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"\n✓ Test file created: {output_path}")
    print(f"\nThis file uses the CORRECT PremiereData format!")
    print(f"First style modified: RGB(0,114,255) → RGB(100,200,255)")
    print(f"Other 9 styles unchanged")
    print(f"\nPlease test in Premiere Pro!")

if __name__ == "__main__":
    modify_premiere_file()
