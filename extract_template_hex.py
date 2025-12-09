#!/usr/bin/env python3
"""
テンプレート .prtextstyle ファイルの詳細 hex dump 抽出ツール
"""

import xml.etree.ElementTree as ET
import base64
import zlib
from pathlib import Path
from typing import Optional, List, Tuple


class TemplateHexExtractor:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = Path(filepath).name
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
        self.encoded_data: Optional[str] = None
        self.decoded_data: Optional[bytes] = None
        self.binary_data: Optional[bytes] = None

    def extract_base64(self) -> str:
        """StartKeyframeValueタグからbase64文字列を抽出"""
        for elem in self.root.iter():
            if elem.tag == 'StartKeyframeValue' and elem.get('Encoding') == 'base64':
                if elem.text:
                    self.encoded_data = elem.text.strip()
                    return self.encoded_data
        raise ValueError("StartKeyframeValue (base64) not found")

    def decode_binary(self) -> bytes:
        """base64をデコードし、必要に応じてzlib解凍"""
        if not self.encoded_data:
            self.extract_base64()

        self.decoded_data = base64.b64decode(self.encoded_data)

        # zlib解凍を試みる
        try:
            self.binary_data = zlib.decompress(self.decoded_data)
            return self.binary_data
        except zlib.error:
            self.binary_data = self.decoded_data
            return self.binary_data

    def hex_dump_xxd(self, data: bytes, start_offset: int = 0,
                     num_bytes: int = None) -> str:
        """xxd形式のhex dumpを生成"""
        if num_bytes:
            data = data[start_offset:start_offset + num_bytes]
            offset = start_offset
        else:
            offset = 0

        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            # 16バイトに満たない場合はスペースで埋める
            hex_part += "   " * (16 - len(chunk))

            # ASCII部分（印字可能文字のみ）
            ascii_part = "".join(
                chr(b) if 32 <= b < 127 else "." for b in chunk
            )

            lines.append(f"{offset + i:08x}: {hex_part}  {ascii_part}")

        return "\n".join(lines)

    def find_pattern(self, pattern: bytes) -> List[int]:
        """特定のバイトパターンの出現位置をすべて検索"""
        positions = []
        offset = 0
        while True:
            pos = self.binary_data.find(pattern, offset)
            if pos == -1:
                break
            positions.append(pos)
            offset = pos + 1
        return positions

    def extract_around_pattern(self, pattern: bytes,
                               before: int = 16,
                               after: int = 16) -> List[Tuple[int, str]]:
        """パターンの前後を抽出してhex dump"""
        positions = self.find_pattern(pattern)
        results = []

        for pos in positions:
            start = max(0, pos - before)
            end = min(len(self.binary_data), pos + len(pattern) + after)
            chunk = self.binary_data[start:end]

            dump = self.hex_dump_xxd(chunk, start_offset=start)
            results.append((pos, dump))

        return results

    def find_gradient_stops(self) -> Optional[List[int]]:
        """GradientStop の推定位置を検索"""
        # 青 (00 00 FF) の位置を基準にする
        blue_positions = self.find_pattern(bytes([0x00, 0x00, 0xFF]))

        if not blue_positions:
            return None

        # グラデーションファイルの場合、青は後半に出現
        grad_candidates = [pos for pos in blue_positions if pos > 0x0200]

        if not grad_candidates:
            return None

        # 各Stop位置を推定（48バイトごと）
        stops = []
        base_pos = grad_candidates[0]

        # Stop0の開始位置を推定（RGBの少し前）
        stop0_start = base_pos - 8  # 推定オフセット調整
        stops.append(stop0_start)

        # Stop1, Stop2...
        for i in range(1, 4):  # 最大4 Stops
            next_stop = stop0_start + (48 * i)
            if next_stop < len(self.binary_data):
                stops.append(next_stop)

        return stops

    def analyze(self):
        """完全解析を実行"""
        print(f"{'='*80}")
        print(f"ファイル: {self.filename}")
        print(f"{'='*80}\n")

        # 1. Base64抽出
        self.extract_base64()
        print(f"[1] Base64 文字列（最初の100文字）:")
        print(f"    {self.encoded_data[:100]}...\n")

        # 2. バイナリデコード
        self.decode_binary()
        print(f"[2] デコード後のバイナリサイズ: {len(self.binary_data)} bytes\n")

        # 3. 全体の hex dump（最初の256バイト）
        print(f"[3] 全体 Hex Dump（先頭256バイト）:")
        print(self.hex_dump_xxd(self.binary_data[:256]))
        print()

        # 4. 青 (00 00 FF) の検索
        print(f"[4A] 青 (00 00 FF) の最初の出現:")
        blue_results = self.extract_around_pattern(bytes([0x00, 0x00, 0xFF]))
        if blue_results:
            pos, dump = blue_results[0]
            print(f"     オフセット: 0x{pos:04X}")
            print(dump)
            print()
        else:
            print("     → 見つかりませんでした\n")

        # 5. 白 (FF FF FF) の検索
        print(f"[4B] 白 (FF FF FF) の最初の出現:")
        white_results = self.extract_around_pattern(bytes([0xFF, 0xFF, 0xFF]))
        if white_results:
            pos, dump = white_results[0]
            print(f"     オフセット: 0x{pos:04X}")
            print(dump)
            print()
        else:
            print("     → 見つかりませんでした\n")

        # 6. 黒 (00 00 00) の検索（Stroke用）
        print(f"[4D] 黒 (00 00 00) の最初の出現:")
        black_results = self.extract_around_pattern(bytes([0x00, 0x00, 0x00]))
        if black_results:
            pos, dump = black_results[0]
            print(f"     オフセット: 0x{pos:04X}")
            print(dump)
            print()
        else:
            print("     → 見つかりませんでした\n")

        # 7. GradientStop の推定位置
        print(f"[4C] GradientStop 推定位置（各Stopの前後32バイト）:")
        stop_positions = self.find_gradient_stops()
        if stop_positions:
            for i, stop_pos in enumerate(stop_positions):
                print(f"\n     Stop{i} 開始位置: 0x{stop_pos:04X}")
                start = max(0, stop_pos - 32)
                end = min(len(self.binary_data), stop_pos + 32)
                chunk = self.binary_data[start:end]
                print(self.hex_dump_xxd(chunk, start_offset=start))
        else:
            print("     → GradientStop なし（単色Fill）\n")

        print(f"\n{'='*80}\n")


def main():
    # テンプレートファイルのリスト（直接ファイル名を使用）
    templates = [
        "TEMPLATE_SolidFill_White.prtextstyle",
        "TEMPLATE_Grad2_BlueToWhite.prtextstyle",
        "TEMPLATE_Grad3_BlueWhiteRed.prtextstyle",
        "TEMPLATE_SolidFill_White_StrokeBlack.prtextstyle",
        "TEMPLATE_Grad3_BlueWhiteRed_StrokeBlack.prtextstyle",
    ]

    print("\n" + "="*80)
    print("prtextstyle テンプレート Hex Dump 抽出ツール")
    print("="*80 + "\n")

    # 解析実行
    for template_name in templates:
        if Path(template_name).exists():
            extractor = TemplateHexExtractor(template_name)
            extractor.analyze()
        else:
            print(f"⚠️  {template_name} が見つかりません\n")


if __name__ == "__main__":
    main()
