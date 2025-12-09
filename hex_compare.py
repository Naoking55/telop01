#!/usr/bin/env python3
"""
Hexダンプ比較ツール - サイドバイサイド表示
"""

import base64
import zlib
import xml.etree.ElementTree as ET
import struct
from pathlib import Path


def extract_binary_from_prtextstyle(file_path: str) -> bytes:
    """prtextstyleファイルからバイナリデータを抽出"""
    tree = ET.parse(file_path)
    root = tree.getroot()

    for elem in root.iter():
        if elem.tag == 'StartKeyframeValue' and elem.get('Encoding') == 'base64':
            if elem.text:
                encoded = elem.text.strip()
                decoded = base64.b64decode(encoded)
                try:
                    return zlib.decompress(decoded)
                except:
                    return decoded
    return None


def hex_line(data: bytes, offset: int) -> str:
    """1行分のhex文字列を生成"""
    chunk = data[offset:min(offset + 16, len(data))]
    return " ".join(f"{b:02X}" for b in chunk).ljust(47)


def compare_hex_side_by_side(name1: str, data1: bytes, name2: str, data2: bytes,
                              start: int = 0, lines: int = 32):
    """2つのバイナリをサイドバイサイドで比較表示"""
    print(f"\n{'='*100}")
    print(f"Hex比較: {name1} vs {name2}")
    print(f"オフセット: 0x{start:04X} - 0x{start + lines*16:04X}")
    print(f"{'='*100}\n")

    print(f"{'Offset':<10} {'  ' + name1:<50} {'  ' + name2:<50} Diff")
    print("-" * 100)

    for i in range(lines):
        offset = start + i * 16

        # データ1の行
        if offset < len(data1):
            hex1 = hex_line(data1, offset)
        else:
            hex1 = " " * 47

        # データ2の行
        if offset < len(data2):
            hex2 = hex_line(data2, offset)
        else:
            hex2 = " " * 47

        # 差分チェック
        diff = ""
        if offset < min(len(data1), len(data2)):
            for j in range(16):
                if offset + j < len(data1) and offset + j < len(data2):
                    if data1[offset + j] != data2[offset + j]:
                        diff = "  <-- DIFF"
                        break

        print(f"0x{offset:04X}     {hex1}  {hex2}{diff}")


def find_all_differences(data1: bytes, data2: bytes) -> list:
    """すべての差分オフセットをリスト化"""
    min_len = min(len(data1), len(data2))
    diffs = []

    for i in range(min_len):
        if data1[i] != data2[i]:
            diffs.append(i)

    return diffs


def analyze_diff_context(data1: bytes, data2: bytes, offset: int, name1: str, name2: str):
    """差分箇所の周辺を詳細解析"""
    print(f"\n差分オフセット: 0x{offset:04X} ({offset})")
    print("-" * 60)

    # バイト値
    print(f"{name1}: 0x{data1[offset]:02X} ({data1[offset]:3d})")
    print(f"{name2}: 0x{data2[offset]:02X} ({data2[offset]:3d})")

    # 4バイト境界の場合、float32として解釈
    if offset % 4 == 0 and offset + 4 <= min(len(data1), len(data2)):
        f1 = struct.unpack('<f', data1[offset:offset+4])[0]
        f2 = struct.unpack('<f', data2[offset:offset+4])[0]
        print(f"Float32: {f1:.6f} vs {f2:.6f}")

        # 0-1範囲ならRGB成分の可能性
        if 0 <= f1 <= 1 and 0 <= f2 <= 1:
            print(f"  → RGB成分の可能性: {f1*255:.1f}/255 vs {f2*255:.1f}/255")

    print()


if __name__ == "__main__":
    # ファイル読み込み
    red_data = extract_binary_from_prtextstyle("赤・ストローク無し.prtextstyle")
    blue_data = extract_binary_from_prtextstyle("青・ストローク無し.prtextstyle")

    if red_data and blue_data:
        print(f"赤ファイルサイズ: {len(red_data)} bytes")
        print(f"青ファイルサイズ: {len(blue_data)} bytes")
        print()

        # 差分オフセットを全リスト
        diffs = find_all_differences(red_data, blue_data)
        print(f"差分バイト数: {len(diffs)}")
        print(f"差分オフセット: {[f'0x{d:04X}' for d in diffs[:20]]}")
        if len(diffs) > 20:
            print(f"  ... 他 {len(diffs) - 20} 箇所")
        print()

        # 全体をサイドバイサイドで比較（いくつかのセクション）
        compare_hex_side_by_side("赤", red_data, "青", blue_data, start=0x0000, lines=16)
        compare_hex_side_by_side("赤", red_data, "青", blue_data, start=0x0100, lines=16)
        compare_hex_side_by_side("赤", red_data, "青", blue_data, start=0x0140, lines=16)
        compare_hex_side_by_side("赤", red_data, "青", blue_data, start=0x0180, lines=16)

        # 主要な差分箇所の詳細解析
        print("\n" + "="*100)
        print("主要差分の詳細解析")
        print("="*100)

        # 4バイト境界にある差分のみ抽出（float32の可能性）
        significant_diffs = [d for d in diffs if d % 4 == 0]
        print(f"\n4バイト境界の差分: {len(significant_diffs)} 箇所")

        for offset in significant_diffs[:10]:
            analyze_diff_context(red_data, blue_data, offset, "赤", "青")

    print("\n" + "="*100)
    print("グラデーション比較")
    print("="*100)

    grad2_data = extract_binary_from_prtextstyle("青白グラ・ストローク無し.prtextstyle")
    grad3_data = extract_binary_from_prtextstyle("青白赤グラ・ストローク無し.prtextstyle")

    if grad2_data and grad3_data:
        print(f"\n2色グラデサイズ: {len(grad2_data)} bytes")
        print(f"3色グラデサイズ: {len(grad3_data)} bytes")
        print(f"サイズ差: {len(grad3_data) - len(grad2_data)} bytes")
        print()

        compare_hex_side_by_side("2色グラデ", grad2_data, "3色グラデ", grad3_data, start=0x0000, lines=16)
        compare_hex_side_by_side("2色グラデ", grad2_data, "3色グラデ", grad3_data, start=0x0100, lines=24)
        compare_hex_side_by_side("2色グラデ", grad2_data, "3色グラデ", grad3_data, start=0x0200, lines=16)

    print("\n" + "="*100)
    print("Stroke比較（黄 vs 水色）")
    print("="*100)

    yellow_data = extract_binary_from_prtextstyle("白・エッジ黄.prtextstyle")
    cyan_data = extract_binary_from_prtextstyle("白・水エッジ.prtextstyle")

    if yellow_data and cyan_data:
        print(f"\n黄エッジサイズ: {len(yellow_data)} bytes")
        print(f"水色エッジサイズ: {len(cyan_data)} bytes")
        print()

        compare_hex_side_by_side("黄エッジ", yellow_data, "水色エッジ", cyan_data, start=0x0000, lines=16)
        compare_hex_side_by_side("黄エッジ", yellow_data, "水色エッジ", cyan_data, start=0x0100, lines=20)
        compare_hex_side_by_side("黄エッジ", yellow_data, "水色エッジ", cyan_data, start=0x0180, lines=16)

        # Stroke色の差分
        diffs_stroke = find_all_differences(yellow_data, cyan_data)
        print(f"\nStroke差分バイト数: {len(diffs_stroke)}")

        # 4バイト境界の差分
        significant_stroke = [d for d in diffs_stroke if d % 4 == 0]
        print(f"4バイト境界の差分: {len(significant_stroke)} 箇所\n")

        for offset in significant_stroke[:10]:
            analyze_diff_context(yellow_data, cyan_data, offset, "黄", "水色")
