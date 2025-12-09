#!/usr/bin/env python3
"""
.prtextstyle ファイルのバイナリ解析ツール

目的：
- base64エンコードされたデータを抽出
- zlibデコード（必要に応じて）
- hexダンプで確認
- 複数ファイルの差分比較
"""

import base64
import zlib
import xml.etree.ElementTree as ET
import sys
from pathlib import Path
from typing import Dict, Tuple, List
import struct


class PrtextstyleAnalyzer:
    """prtextstyleファイルの解析クラス"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()
        self.encoded_data = None
        self.decoded_data = None
        self.binary_data = None

    def extract_base64(self) -> str:
        """StartKeyframeValueタグからbase64文字列を抽出"""
        # まずStartKeyframeValueを探す（スタイル情報が含まれる）
        for elem in self.root.iter():
            if elem.tag == 'StartKeyframeValue' and elem.get('Encoding') == 'base64':
                if elem.text:
                    self.encoded_data = elem.text.strip()
                    return self.encoded_data

        # 見つからない場合は従来のEncodedDataも試す
        encoded_elem = self.root.find(".//EncodedData")
        if encoded_elem is not None and encoded_elem.text:
            self.encoded_data = encoded_elem.text.strip()
            return self.encoded_data
        return None

    def decode_binary(self) -> bytes:
        """base64をデコードし、必要に応じてzlib解凍"""
        if not self.encoded_data:
            self.extract_base64()

        if not self.encoded_data:
            raise ValueError("EncodedData not found")

        # base64デコード
        self.decoded_data = base64.b64decode(self.encoded_data)

        # zlib圧縮されているか確認してデコード
        try:
            self.binary_data = zlib.decompress(self.decoded_data)
            print(f"✓ zlib圧縮あり（解凍後サイズ: {len(self.binary_data)} bytes）")
        except zlib.error:
            # 圧縮されていない場合
            self.binary_data = self.decoded_data
            print(f"✓ zlib圧縮なし（サイズ: {len(self.binary_data)} bytes）")

        return self.binary_data

    def hex_dump(self, data: bytes = None, start: int = 0, length: int = None,
                 bytes_per_line: int = 16) -> str:
        """バイナリデータをhexダンプ形式で表示"""
        if data is None:
            data = self.binary_data

        if data is None:
            return "No binary data available"

        if length is None:
            length = len(data) - start

        end = min(start + length, len(data))
        lines = []

        for i in range(start, end, bytes_per_line):
            # オフセット
            offset = f"{i:08X}"

            # Hexバイト
            chunk = data[i:min(i + bytes_per_line, end)]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            hex_part = hex_part.ljust(bytes_per_line * 3 - 1)

            # ASCII部分（印字可能文字のみ）
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)

            lines.append(f"{offset}  {hex_part}  |{ascii_part}|")

        return "\n".join(lines)

    def find_float32_values(self, data: bytes = None, min_val: float = 0.0,
                           max_val: float = 1.0) -> List[Tuple[int, float]]:
        """float32値（0.0-1.0範囲など）を検索"""
        if data is None:
            data = self.binary_data

        results = []
        for i in range(len(data) - 3):
            try:
                val = struct.unpack('<f', data[i:i+4])[0]  # リトルエンディアン
                if min_val <= val <= max_val:
                    results.append((i, val))
            except:
                pass

        return results

    def compare_binary(self, other: 'PrtextstyleAnalyzer') -> List[Tuple[int, int, int]]:
        """2つのバイナリデータを比較し、差分を返す"""
        if self.binary_data is None or other.binary_data is None:
            raise ValueError("Binary data not available")

        min_len = min(len(self.binary_data), len(other.binary_data))
        differences = []

        i = 0
        while i < min_len:
            if self.binary_data[i] != other.binary_data[i]:
                # 差分の開始位置
                start = i
                # 連続する差分をグループ化
                while i < min_len and self.binary_data[i] != other.binary_data[i]:
                    i += 1
                differences.append((start, i - start, i))
            else:
                i += 1

        return differences

    def extract_style_info(self) -> Dict:
        """XMLからスタイル情報を抽出"""
        info = {
            'name': 'Unknown',
            'uid': None,
        }

        # StyleProjectItem内のNameを探す
        style_item = self.root.find(".//StyleProjectItem")
        if style_item is not None:
            name_elem = style_item.find(".//Name")
            if name_elem is not None and name_elem.text:
                info['name'] = name_elem.text.strip()

            uid = style_item.get('ObjectUID')
            if uid:
                info['uid'] = uid

        return info


def compare_files_detailed(file1_path: str, file2_path: str,
                          context_bytes: int = 32):
    """2つのファイルを詳細に比較"""
    print(f"\n{'='*80}")
    print(f"比較: {Path(file1_path).name} vs {Path(file2_path).name}")
    print(f"{'='*80}\n")

    analyzer1 = PrtextstyleAnalyzer(file1_path)
    analyzer2 = PrtextstyleAnalyzer(file2_path)

    # スタイル情報
    info1 = analyzer1.extract_style_info()
    info2 = analyzer2.extract_style_info()
    print(f"ファイル1: {info1['name']}")
    print(f"ファイル2: {info2['name']}")
    print()

    # バイナリデコード
    data1 = analyzer1.decode_binary()
    data2 = analyzer2.decode_binary()

    print(f"サイズ比較: {len(data1)} bytes vs {len(data2)} bytes")
    print()

    # 差分検出
    differences = analyzer1.compare_binary(analyzer2)

    print(f"差分箇所: {len(differences)} 個\n")

    for idx, (offset, length, end) in enumerate(differences[:20], 1):  # 最初の20個
        print(f"--- 差分 #{idx} ---")
        print(f"オフセット: 0x{offset:04X} - 0x{end:04X} ({length} bytes)\n")

        # コンテキスト付きでhexダンプ
        start_ctx = max(0, offset - context_bytes)
        end_ctx = min(len(data1), end + context_bytes)

        print("ファイル1:")
        print(analyzer1.hex_dump(start=start_ctx, length=end_ctx-start_ctx))
        print("\nファイル2:")
        print(analyzer2.hex_dump(start=start_ctx, length=end_ctx-start_ctx))

        # float32として解釈を試みる（4バイトの差分の場合）
        if length == 4:
            try:
                val1 = struct.unpack('<f', data1[offset:offset+4])[0]
                val2 = struct.unpack('<f', data2[offset:offset+4])[0]
                print(f"\nfloat32解釈: {val1:.6f} → {val2:.6f}")
            except:
                pass

        print("\n")

    if len(differences) > 20:
        print(f"（残り {len(differences) - 20} 個の差分は省略）")

    return analyzer1, analyzer2, differences


def analyze_single_file(file_path: str, dump_length: int = 512):
    """単一ファイルを解析"""
    print(f"\n{'='*80}")
    print(f"解析: {Path(file_path).name}")
    print(f"{'='*80}\n")

    analyzer = PrtextstyleAnalyzer(file_path)

    # スタイル情報
    info = analyzer.extract_style_info()
    print(f"スタイル名: {info['name']}")
    print(f"UID: {info['uid']}")
    print()

    # バイナリデコード
    data = analyzer.decode_binary()
    print(f"データサイズ: {len(data)} bytes")
    print()

    # Hexダンプ（最初の部分）
    print(f"Hexダンプ（最初の{dump_length}バイト）:")
    print(analyzer.hex_dump(length=dump_length))
    print()

    # 0.0-1.0範囲のfloat32値を探す（色値の可能性）
    float_values = analyzer.find_float32_values(min_val=-0.1, max_val=1.1)
    print(f"\n0.0-1.0範囲のfloat32候補: {len(float_values)} 個")
    print("最初の20個:")
    for offset, value in float_values[:20]:
        print(f"  0x{offset:04X}: {value:.6f}")

    return analyzer


if __name__ == "__main__":
    import os

    # カレントディレクトリの.prtextstyleファイルを列挙
    prtextstyle_files = sorted(Path(".").glob("*.prtextstyle"))

    if not prtextstyle_files:
        print("エラー: .prtextstyleファイルが見つかりません")
        sys.exit(1)

    print("\n見つかったファイル:")
    for i, f in enumerate(prtextstyle_files, 1):
        print(f"  {i}. {f.name}")

    # すべてのファイルを解析
    print("\n" + "="*80)
    print("Step 1: 個別ファイル解析")
    print("="*80)

    analyzers = {}
    for file in prtextstyle_files:
        analyzer = analyze_single_file(str(file))
        analyzers[file.name] = analyzer

    # 特定のペアで差分比較
    print("\n" + "="*80)
    print("Step 2: 差分比較")
    print("="*80)

    # 赤 vs 青（単色Fill比較）
    red_file = "赤・ストローク無し.prtextstyle"
    blue_file = "青・ストローク無し.prtextstyle"
    if red_file in analyzers and blue_file in analyzers:
        print("\n### 比較1: 赤 vs 青（単色Fill）###")
        compare_files_detailed(red_file, blue_file, context_bytes=16)

    # 青白グラ vs 青白赤グラ（グラデーション比較）
    grad2_file = "青白グラ・ストローク無し.prtextstyle"
    grad3_file = "青白赤グラ・ストローク無し.prtextstyle"
    if grad2_file in analyzers and grad3_file in analyzers:
        print("\n### 比較2: 2色グラデ vs 3色グラデ ###")
        compare_files_detailed(grad2_file, grad3_file, context_bytes=16)

    # 白・エッジ黄 vs 白・水エッジ（Stroke比較）
    yellow_stroke = "白・エッジ黄.prtextstyle"
    cyan_stroke = "白・水エッジ.prtextstyle"
    if yellow_stroke in analyzers and cyan_stroke in analyzers:
        print("\n### 比較3: 黄ストローク vs 水色ストローク ###")
        compare_files_detailed(yellow_stroke, cyan_stroke, context_bytes=16)
