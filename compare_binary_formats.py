#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
複数の prtextstyle ファイルのバイナリデータを比較して構造を解明
"""

from xml.etree import ElementTree as ET
import base64
import struct
import sys
from typing import Dict, List, Tuple
from difflib import SequenceMatcher

def extract_binary_from_prtextstyle(filepath: str) -> List[Tuple[str, bytes]]:
    """prtextstyle から全てのバイナリデータを抽出"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    binaries = []

    # ArbVideoComponentParam を探す
    for param in root.findall(".//ArbVideoComponentParam"):
        name_elem = param.find("Name")
        name = name_elem.text if name_elem is not None else "?"

        keyframe_val = param.find("StartKeyframeValue")
        if keyframe_val is not None and keyframe_val.text:
            encoding = keyframe_val.attrib.get('Encoding', '')
            if encoding == 'base64':
                try:
                    binary = base64.b64decode(keyframe_val.text.strip())
                    binaries.append((name, binary))
                except:
                    pass

    return binaries

def hex_dump(data: bytes, offset: int = 0, length: int = None) -> str:
    """バイナリデータを16進数でダンプ"""
    if length is not None:
        data = data[:length]

    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"{offset+i:04x}:  {hex_part:<48}  {ascii_part}")

    return '\n'.join(lines)

def compare_binaries(bin1: bytes, bin2: bytes, name1: str, name2: str):
    """2つのバイナリを比較して差分を表示"""
    print(f"\n{'='*80}")
    print(f"比較: {name1} vs {name2}")
    print(f"{'='*80}")
    print(f"サイズ: {len(bin1)} bytes vs {len(bin2)} bytes")

    # 同じ部分と異なる部分を見つける
    matcher = SequenceMatcher(None, bin1, bin2)

    print("\n差分の概要:")
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            print(f"  0x{i1:04x}-0x{i2:04x}: 同一 ({i2-i1} bytes)")
        elif tag == 'replace':
            print(f"  0x{i1:04x}-0x{i2:04x}: 差異")
            print(f"    {name1}: {bin1[i1:i2][:16].hex()}...")
            print(f"    {name2}: {bin2[j1:j2][:16].hex()}...")
        elif tag == 'delete':
            print(f"  0x{i1:04x}-0x{i2:04x}: {name1} のみ")
        elif tag == 'insert':
            print(f"  0x{j1:04x}-0x{j2:04x}: {name2} のみ")

def find_color_values(binary: bytes) -> List[Tuple[int, str]]:
    """色の値を探す（0.0-1.0 のfloat、0-255の整数）"""
    candidates = []

    # Float (0.0-1.0)
    for i in range(len(binary) - 3):
        try:
            f = struct.unpack("<f", binary[i:i+4])[0]
            if 0.0 <= f <= 1.0:
                candidates.append((i, f"float:{f:.3f}"))
        except:
            pass

    # Byte (0-255)
    for i in range(len(binary)):
        b = binary[i]
        if 0 <= b <= 255:
            candidates.append((i, f"byte:{b}"))

    return candidates

def analyze_structure(binary: bytes, name: str):
    """バイナリの構造を解析"""
    print(f"\n{'='*80}")
    print(f"構造解析: {name}")
    print(f"{'='*80}")
    print(f"サイズ: {len(binary)} bytes")

    # 最初の256バイトを表示
    print("\n最初の256バイト:")
    print(hex_dump(binary, length=256))

    # 文字列を探す
    print("\n\n文字列の検出:")
    offset = 0
    while offset < len(binary) - 4:
        # 長さフィールド候補（4バイトのuint32）
        if offset + 4 <= len(binary):
            length = struct.unpack("<I", binary[offset:offset+4])[0]

            # 妥当な長さ（1-1000）
            if 1 < length < 1000:
                if offset + 4 + length <= len(binary):
                    potential_str = binary[offset+4:offset+4+length]
                    try:
                        decoded = potential_str.decode('utf-8')
                        # 印字可能文字が多い
                        if sum(32 <= b < 127 for b in potential_str) > length * 0.7:
                            print(f"  0x{offset:04x}: 長さ={length}, 文字列='{decoded}'")
                    except:
                        pass

        offset += 1

    # 色候補を探す（連続する4つのfloat: R,G,B,A）
    print("\n\n色の候補（連続4個のfloat）:")
    for i in range(0, len(binary) - 15, 4):
        try:
            r, g, b, a = struct.unpack("<ffff", binary[i:i+16])
            # 全て0.0-1.0の範囲
            if all(0.0 <= v <= 1.0 for v in [r, g, b, a]):
                # 全て0.0や全て1.0は除外
                if not (all(v == 0.0 for v in [r, g, b, a]) or all(v == 1.0 for v in [r, g, b, a])):
                    print(f"  0x{i:04x}: R={r:.3f}, G={g:.3f}, B={b:.3f}, A={a:.3f}")
        except:
            pass

def main():
    # 解析対象ファイル
    files = [
        ("White", "TEMPLATE_SolidFill_White.prtextstyle"),
        ("Red", "赤・ストローク無し.prtextstyle"),
        ("Blue", "青・ストローク無し.prtextstyle"),
        ("GradBlueWhite", "青白グラ・ストローク無し.prtextstyle"),
        ("WhiteStroke", "TEMPLATE_SolidFill_White_StrokeBlack.prtextstyle"),
    ]

    all_binaries = {}

    print("="*80)
    print("prtextstyle バイナリフォーマット完全解析")
    print("="*80)

    # 全ファイルからバイナリを抽出
    for label, filepath in files:
        try:
            binaries = extract_binary_from_prtextstyle(filepath)
            if binaries:
                # 最初のバイナリ（Source Textのはず）
                name, binary = binaries[0]
                all_binaries[label] = binary
                print(f"\n✓ {label}: {len(binary)} bytes (from {name})")
        except Exception as e:
            print(f"\n✗ {label}: エラー - {e}")

    if not all_binaries:
        print("\nバイナリデータが見つかりませんでした")
        return

    # 基準ファイル（White）
    if "White" not in all_binaries:
        print("\n基準ファイル(White)が見つかりません")
        return

    base_binary = all_binaries["White"]

    # Whiteの構造を詳細解析
    analyze_structure(base_binary, "White (基準)")

    # 他のファイルと比較
    for label, binary in all_binaries.items():
        if label != "White":
            compare_binaries(base_binary, binary, "White", label)

    # 特定の色の検出
    print("\n\n" + "="*80)
    print("色の値の特定")
    print("="*80)

    # 赤の検出
    if "Red" in all_binaries:
        print("\n[赤のファイル]")
        analyze_structure(all_binaries["Red"], "Red")

    # 青の検出
    if "Blue" in all_binaries:
        print("\n[青のファイル]")
        analyze_structure(all_binaries["Blue"], "Blue")

    # ストロークありの検出
    if "WhiteStroke" in all_binaries:
        print("\n[ストロークありのファイル]")
        analyze_structure(all_binaries["WhiteStroke"], "White with Stroke")

        # WhiteとWhiteStrokeの差分
        compare_binaries(all_binaries["White"], all_binaries["WhiteStroke"],
                        "White (No Stroke)", "White (With Stroke)")

    print("\n\n" + "="*80)
    print("✅ 解析完了")
    print("="*80)

if __name__ == "__main__":
    main()
