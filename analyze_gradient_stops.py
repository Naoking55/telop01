#!/usr/bin/env python3
"""
グラデーションストップ位置の解析
青白赤グラ 30 vs 70 の比較
"""

import xml.etree.ElementTree as ET
import base64
import struct
from pathlib import Path

def get_binary_from_prtextstyle(filepath):
    """prtextstyleファイルからバイナリを取得"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    # ArbVideoComponentParamを探す
    for arb_param in root.findall('.//ArbVideoComponentParam'):
        name_elem = arb_param.find('.//Name')
        if name_elem is not None and ('Source Text' in name_elem.text or 'ソーステキスト' in name_elem.text):
            binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
            if binary_elem is not None and binary_elem.text:
                return base64.b64decode(binary_elem.text.strip())

    return None

def find_float_differences(bin1, bin2, min_val=0.0, max_val=1.0):
    """2つのバイナリでfloat値が異なる位置を検出"""
    differences = []

    min_len = min(len(bin1), len(bin2))

    for offset in range(0, min_len - 3, 4):
        try:
            val1 = struct.unpack('<f', bin1[offset:offset+4])[0]
            val2 = struct.unpack('<f', bin2[offset:offset+4])[0]

            # 両方が指定範囲内のfloat値で、かつ異なる
            if (min_val <= val1 <= max_val and
                min_val <= val2 <= max_val and
                abs(val1 - val2) > 0.001):
                differences.append((offset, val1, val2))
        except:
            pass

    return differences

def main():
    import glob

    # globでファイルを探す
    files_30 = glob.glob("prtextstyle/*30.prtextstyle")
    files_70 = glob.glob("prtextstyle/*70.prtextstyle")

    file_30 = [f for f in files_30 if '30' in f and '70' not in f][0]
    file_70 = [f for f in files_70 if '70' in f][0]

    print(f"File 30: {file_30}")
    print(f"File 70: {file_70}")
    print()

    print("="*80)
    print("グラデーションストップ位置の解析")
    print("="*80)
    print()

    bin_30 = get_binary_from_prtextstyle(file_30)
    bin_70 = get_binary_from_prtextstyle(file_70)

    if not bin_30 or not bin_70:
        print("❌ バイナリの取得に失敗")
        return

    print(f"青白赤グラ 30: {len(bin_30)} bytes")
    print(f"青白赤グラ 70: {len(bin_70)} bytes")
    print()

    # float値の違いを検出（0.0-1.0範囲）
    print("="*80)
    print("float値の違い（0.0-1.0範囲）:")
    print("="*80)
    print()

    differences = find_float_differences(bin_30, bin_70, 0.0, 1.0)

    print(f"検出された違い: {len(differences)} 箇所\n")

    for i, (offset, val1, val2) in enumerate(differences, 1):
        # 0.3 or 0.7 に近い値をハイライト
        marker = ""
        if abs(val1 - 0.3) < 0.01 or abs(val2 - 0.7) < 0.01:
            marker = " ★ グラデーションストップ位置の可能性！"
        elif abs(val1 - 0.7) < 0.01 or abs(val2 - 0.3) < 0.01:
            marker = " ★ グラデーションストップ位置の可能性！"

        print(f"{i:2d}. 0x{offset:04x}:")
        print(f"    30ファイル: {val1:.6f}")
        print(f"    70ファイル: {val2:.6f}")
        print(f"    差分: {abs(val2-val1):.6f}{marker}")
        print()

    # 0.3付近の値を持つ位置を探す（30ファイル）
    print("="*80)
    print("30ファイルで0.3に近い値:")
    print("="*80)
    print()

    for offset in range(0, len(bin_30) - 3, 4):
        try:
            val = struct.unpack('<f', bin_30[offset:offset+4])[0]
            if abs(val - 0.3) < 0.01:
                hex_context = bin_30[max(0, offset-8):offset+12].hex()
                print(f"0x{offset:04x}: {val:.6f}")
                print(f"  Context: {hex_context}")
                print()
        except:
            pass

    # 0.7付近の値を持つ位置を探す（70ファイル）
    print("="*80)
    print("70ファイルで0.7に近い値:")
    print("="*80)
    print()

    for offset in range(0, len(bin_70) - 3, 4):
        try:
            val = struct.unpack('<f', bin_70[offset:offset+4])[0]
            if abs(val - 0.7) < 0.01:
                hex_context = bin_70[max(0, offset-8):offset+12].hex()
                print(f"0x{offset:04x}: {val:.6f}")
                print(f"  Context: {hex_context}")
                print()
        except:
            pass

if __name__ == "__main__":
    main()
