#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参考ファイルの詳細解析 - フォントサイズ、グラデーションストップ位置の特定
"""

from xml.etree import ElementTree as ET
import base64
import struct
import os
from pathlib import Path

def extract_binary(filepath: str) -> bytes:
    """prtextstyle からバイナリデータを抽出"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    for param in root.findall(".//ArbVideoComponentParam"):
        name_elem = param.find("Name")
        if name_elem is not None and name_elem.text == "ソーステキスト":
            keyframe_val = param.find("StartKeyframeValue")
            if keyframe_val is not None and keyframe_val.text:
                encoding = keyframe_val.attrib.get('Encoding', '')
                if encoding == 'base64':
                    return base64.b64decode(keyframe_val.text.strip())
    return b""

def find_float_values(binary: bytes, min_val: float = -100.0, max_val: float = 400.0) -> list:
    """float値を探す"""
    candidates = []
    for i in range(0, len(binary) - 3, 4):
        try:
            f = struct.unpack("<f", binary[i:i+4])[0]
            if min_val <= f <= max_val and not (f == 0.0):
                candidates.append((i, f))
        except:
            pass
    return candidates

def compare_two_files(file1: str, file2: str, name1: str, name2: str):
    """2つのファイルを比較"""
    print(f"\n{'='*80}")
    print(f"比較: {name1} vs {name2}")
    print(f"{'='*80}")

    bin1 = extract_binary(file1)
    bin2 = extract_binary(file2)

    if not bin1 or not bin2:
        print("バイナリデータが取得できませんでした")
        return

    print(f"{name1}: {len(bin1)} bytes")
    print(f"{name2}: {len(bin2)} bytes")
    print(f"差分: {len(bin2) - len(bin1)} bytes")

    # サイズが同じ場合は差分を探す
    if len(bin1) == len(bin2):
        print("\n差分箇所:")
        diff_count = 0
        for i in range(len(bin1)):
            if bin1[i] != bin2[i]:
                diff_count += 1
                if diff_count <= 20:  # 最初の20箇所
                    # 周辺を表示
                    if diff_count == 1 or i - prev_diff > 10:
                        context_start = max(0, i - 8)
                        context_end = min(len(bin1), i + 24)

                        print(f"\n  0x{i:04x}:")
                        hex1 = ' '.join(f'{b:02x}' for b in bin1[context_start:context_end])
                        hex2 = ' '.join(f'{b:02x}' for b in bin2[context_start:context_end])
                        print(f"    {name1}: {hex1}")
                        print(f"    {name2}: {hex2}")

                        # float解釈
                        if i + 4 <= len(bin1):
                            try:
                                f1 = struct.unpack("<f", bin1[i:i+4])[0]
                                f2 = struct.unpack("<f", bin2[i:i+4])[0]
                                if -100 <= f1 <= 400 and -100 <= f2 <= 400:
                                    print(f"    Float: {f1:.6f} vs {f2:.6f}")
                            except:
                                pass

                prev_diff = i

        print(f"\n総差分バイト数: {diff_count}")

def analyze_font_sizes():
    """フォントサイズの違いを解析"""
    print("\n" + "="*80)
    print("フォントサイズ解析")
    print("="*80)

    # フォントサイズが30と70のファイル
    file_30 = "prtextstyle/青白赤グラ 30.prtextstyle"
    file_70 = "prtextstyle/青白赤グラ 70.prtextstyle"

    if not os.path.exists(file_30) or not os.path.exists(file_70):
        print("フォントサイズファイルが見つかりません")
        return

    bin_30 = extract_binary(file_30)
    bin_70 = extract_binary(file_70)

    print(f"\nサイズ30: {len(bin_30)} bytes")
    print(f"サイズ70: {len(bin_70)} bytes")

    # float値を探す
    print("\n[サイズ30のfloat値]")
    floats_30 = find_float_values(bin_30, 10.0, 100.0)
    for offset, value in floats_30[:15]:
        if 25 <= value <= 35:  # 30付近
            print(f"  ★ 0x{offset:04x}: {value:.3f}  ← これがフォントサイズ30かも！")
        else:
            print(f"    0x{offset:04x}: {value:.3f}")

    print("\n[サイズ70のfloat値]")
    floats_70 = find_float_values(bin_70, 10.0, 100.0)
    for offset, value in floats_70[:15]:
        if 65 <= value <= 75:  # 70付近
            print(f"  ★ 0x{offset:04x}: {value:.3f}  ← これがフォントサイズ70かも！")
        else:
            print(f"    0x{offset:04x}: {value:.3f}")

    # 詳細比較
    compare_two_files(file_30, file_70, "FontSize30", "FontSize70")

def analyze_gradient_stops():
    """グラデーションストップの解析"""
    print("\n\n" + "="*80)
    print("グラデーションストップ解析")
    print("="*80)

    # 異なるストップ位置のファイル
    files = [
        ("prtextstyle/黄白グラ右50.prtextstyle", "黄白グラ右50"),
        ("prtextstyle/黄白グラ右80.prtextstyle", "黄白グラ右80"),
    ]

    for filepath, name in files:
        if not os.path.exists(filepath):
            continue

        binary = extract_binary(filepath)
        print(f"\n{name} ({len(binary)} bytes):")

        # 0.0-1.0の範囲のfloatを探す（ストップ位置の可能性）
        print("  ストップ位置候補 (0.0-1.0):")
        for i in range(0, len(binary) - 3, 4):
            try:
                f = struct.unpack("<f", binary[i:i+4])[0]
                if 0.0 <= f <= 1.0 and f != 0.0:
                    # 0.5や0.8など、特徴的な値
                    if abs(f - 0.5) < 0.01 or abs(f - 0.8) < 0.01:
                        print(f"    ★ 0x{i:04x}: {f:.6f}")
            except:
                pass

    # 50と80を比較
    if all(os.path.exists(f[0]) for f in files):
        compare_two_files(files[0][0], files[1][0], files[0][1], files[1][1])

def analyze_all_samples():
    """全サンプルの統計"""
    print("\n\n" + "="*80)
    print("全サンプル統計")
    print("="*80)

    prtextstyle_dir = Path("prtextstyle")
    if not prtextstyle_dir.exists():
        print("prtextstyleディレクトリが見つかりません")
        return

    files = list(prtextstyle_dir.glob("*.prtextstyle"))

    print(f"\n総ファイル数: {len(files)}")
    print("\nファイル名とサイズ:")

    samples = []
    for filepath in sorted(files):
        binary = extract_binary(str(filepath))
        if binary:
            samples.append({
                'name': filepath.name,
                'size': len(binary),
                'binary': binary
            })
            print(f"  {filepath.name}: {len(binary)} bytes")

    # サイズの分布
    print("\nサイズ分布:")
    sizes = [s['size'] for s in samples]
    print(f"  最小: {min(sizes)} bytes")
    print(f"  最大: {max(sizes)} bytes")
    print(f"  平均: {sum(sizes)/len(sizes):.1f} bytes")

    # サイズ別グループ
    size_groups = {}
    for s in samples:
        size = s['size']
        if size not in size_groups:
            size_groups[size] = []
        size_groups[size].append(s['name'])

    print("\nサイズ別グループ:")
    for size in sorted(size_groups.keys()):
        names = size_groups[size]
        print(f"  {size} bytes: {len(names)}個")
        for name in names:
            print(f"    - {name}")

def main():
    print("="*80)
    print("参考ファイル詳細解析")
    print("="*80)

    # 全サンプル統計
    analyze_all_samples()

    # フォントサイズ解析
    analyze_font_sizes()

    # グラデーションストップ解析
    analyze_gradient_stops()

    print("\n" + "="*80)
    print("✅ 解析完了")
    print("="*80)

if __name__ == "__main__":
    main()
