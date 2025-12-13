#!/usr/bin/env python3
"""
作成したテストファイルが正しく変更されているか検証
"""

import sys
sys.path.insert(0, '/home/user/telop01')

from prtextstyle_editor import PrtextstyleEditor

MARKER = b'\x02\x00\x00\x00\x41\x61'

def verify_test_file():
    """テストファイルの検証"""

    print("="*80)
    print("Test file verification")
    print("="*80)

    # 元のファイル（Style 1）
    original_editor = PrtextstyleEditor("/tmp/10styles.prtextstyle")
    original_binary = original_editor.get_style_binary(list(original_editor.styles.keys())[0])

    print(f"\nOriginal file (Style 1):")
    print(f"  Expected color: RGB(0, 114, 255)")
    print(f"  Binary size: {len(original_binary)} bytes")

    # マーカー位置
    marker_pos = original_binary.index(MARKER)
    print(f"  Marker position: 0x{marker_pos:04x}")

    # マーカー前のバイト
    color_bytes = original_binary[marker_pos-2:marker_pos]
    print(f"  Bytes before marker: {list(color_bytes)} (should be [0, 114])")

    # テストファイル
    test_editor = PrtextstyleEditor("/home/user/telop01/test_fill_color_RGB_100_200_50.prtextstyle")
    test_style_name = list(test_editor.styles.keys())[0]
    test_binary = test_editor.get_style_binary(test_style_name)

    print(f"\nTest file:")
    print(f"  Style name: {test_style_name}")
    print(f"  Expected color: RGB(100, 200, 255)")
    print(f"  Binary size: {len(test_binary)} bytes")

    # マーカー位置
    test_marker_pos = test_binary.index(MARKER)
    print(f"  Marker position: 0x{test_marker_pos:04x}")

    # マーカー前のバイト
    test_color_bytes = test_binary[test_marker_pos-2:test_marker_pos]
    print(f"  Bytes before marker: {list(test_color_bytes)} (should be [100, 200])")

    # 検証
    print(f"\n{'='*80}")
    print("Verification:")
    print('='*80)

    if list(test_color_bytes) == [100, 200]:
        print("✓ Color bytes are correct!")
    else:
        print(f"✗ Color bytes are WRONG! Expected [100, 200], got {list(test_color_bytes)}")

    if len(test_binary) == len(original_binary):
        print("✓ Binary size is preserved!")
    else:
        print(f"✗ Binary size changed! {len(original_binary)} -> {len(test_binary)}")

    # バイト単位で比較
    differences = []
    min_len = min(len(original_binary), len(test_binary))
    for i in range(min_len):
        if original_binary[i] != test_binary[i]:
            differences.append(i)

    print(f"\nTotal different bytes: {len(differences)}")

    if len(differences) <= 10:
        print(f"Different positions:")
        for pos in differences:
            orig_byte = original_binary[pos] if pos < len(original_binary) else None
            test_byte = test_binary[pos] if pos < len(test_binary) else None
            print(f"  0x{pos:04x}: {orig_byte} -> {test_byte}")

    # ヘックスダンプ比較（マーカー周辺）
    print(f"\n{'='*80}")
    print(f"Hex dump around marker:")
    print('='*80)

    print(f"\nOriginal (0x{marker_pos-16:04x} - 0x{marker_pos+10:04x}):")
    for i in range(marker_pos-16, marker_pos+10, 16):
        bytes_str = ' '.join(f'{original_binary[j]:02x}' for j in range(i, min(i+16, len(original_binary))))
        print(f"  {i:04x}: {bytes_str}")

    print(f"\nTest (0x{test_marker_pos-16:04x} - 0x{test_marker_pos+10:04x}):")
    for i in range(test_marker_pos-16, test_marker_pos+10, 16):
        bytes_str = ' '.join(f'{test_binary[j]:02x}' for j in range(i, min(i+16, len(test_binary))))
        print(f"  {i:04x}: {bytes_str}")

if __name__ == "__main__":
    verify_test_file()
