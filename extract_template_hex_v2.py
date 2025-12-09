#!/usr/bin/env python3
"""
テンプレート .prtextstyle ファイルの詳細 hex dump 抽出ツール v2
- 青・白・Stroke黒の正確な前後16バイト
- GradientStopの前後32バイト
"""

import xml.etree.ElementTree as ET
import base64
import zlib
from pathlib import Path
from typing import Optional, List, Tuple


class TemplateHexExtractorV2:
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

    def hex_dump_xxd(self, data: bytes, start_offset: int = 0) -> str:
        """xxd形式のhex dumpを生成"""
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

            lines.append(f"{start_offset + i:08x}: {hex_part}  {ascii_part}")

        return "\n".join(lines)

    def find_pattern(self, pattern: bytes, start: int = 0) -> Optional[int]:
        """特定のバイトパターンの最初の出現位置を検索"""
        pos = self.binary_data.find(pattern, start)
        return pos if pos != -1 else None

    def extract_exact_around(self, offset: int, before: int = 16, after: int = 16) -> str:
        """指定オフセットの前後を正確に抽出"""
        start = max(0, offset - before)
        end = min(len(self.binary_data), offset + after)
        chunk = self.binary_data[start:end]
        return self.hex_dump_xxd(chunk, start_offset=start)

    def find_stroke_black(self) -> Optional[int]:
        """Stroke領域の黒 (00 00 00) を検索"""
        # Stroke領域は 0x00B0-0x00C0 付近
        stroke_start = 0x00B0
        stroke_end = 0x00C0

        # この範囲内で 00 00 00 を検索
        for offset in range(stroke_start, min(stroke_end, len(self.binary_data) - 3)):
            if (self.binary_data[offset:offset+3] == bytes([0x00, 0x00, 0x00]) and
                # ヘッダの 00 00 00 00 を避けるため、直後が FF でないことを確認
                offset + 3 < len(self.binary_data) and
                self.binary_data[offset+3] != 0x00):
                return offset

        return None

    def find_gradient_stops_accurate(self) -> Optional[List[Tuple[int, int]]]:
        """GradientStop の正確な位置を検索
        Returns: [(stop_number, offset), ...]
        """
        # 青 (00 00 FF) の位置を基準にする
        blue_pos = self.find_pattern(bytes([0x00, 0x00, 0xFF]), 0x0200)

        if not blue_pos:
            return None

        stops = []

        # 青色の前方を探索して、GradientStopの開始位置を推定
        # 通常、RGB値の8バイト前がStop開始
        stop0_start = blue_pos - 8

        # Stop0
        stops.append((0, stop0_start))

        # 48バイトごとにStop1, Stop2を探索
        for i in range(1, 4):
            next_stop = stop0_start + (48 * i)
            if next_stop + 32 < len(self.binary_data):
                # 次のStopが有効な範囲内にあるか確認
                # RGB値があるか確認（簡易チェック）
                if next_stop + 8 + 3 < len(self.binary_data):
                    stops.append((i, next_stop))

        # 実際に存在するStopのみを返す（最大3つまで）
        return stops[:3] if len(stops) <= 3 else stops[:3]

    def analyze(self):
        """完全解析を実行"""
        print(f"{'='*80}")
        print(f"ファイル: {self.filename}")
        print(f"{'='*80}\n")

        # 1. Base64抽出
        self.extract_base64()
        print(f"[1] Base64 文字列（最初の80文字）:")
        print(f"    {self.encoded_data[:80]}...\n")

        # 2. バイナリデコード
        self.decode_binary()
        print(f"[2] デコード後のバイナリサイズ: {len(self.binary_data)} bytes\n")

        # 3. 全体の hex dump（最初の256バイト）
        print(f"[3] 全体 Hex Dump（先頭256バイト）:")
        print(self.hex_dump_xxd(self.binary_data[:256]))
        print()

        # 4A. 青 (00 00 FF) の検索
        print(f"[4A] 青 (00 00 FF) の最初の出現（直前16バイト & 直後16バイト）:")
        blue_pos = self.find_pattern(bytes([0x00, 0x00, 0xFF]))
        if blue_pos:
            print(f"     オフセット: 0x{blue_pos:04X}\n")
            print(self.extract_exact_around(blue_pos, before=16, after=16))
            print()
        else:
            print("     → 見つかりませんでした\n")

        # 4B. 白 (FF FF FF) の検索
        print(f"[4B] 白 (FF FF FF) の最初の出現（直前16バイト & 直後16バイト）:")
        white_pos = self.find_pattern(bytes([0xFF, 0xFF, 0xFF]))
        if white_pos:
            print(f"     オフセット: 0x{white_pos:04X}\n")
            print(self.extract_exact_around(white_pos, before=16, after=16))
            print()
        else:
            print("     → 見つかりませんでした\n")

        # 4D. Stroke黒 (00 00 00) の検索
        print(f"[4D] Stroke 黒 (00 00 00) の最初の出現（直前16バイト & 直後16バイト）:")
        black_pos = self.find_stroke_black()
        if black_pos:
            print(f"     オフセット: 0x{black_pos:04X}\n")
            print(self.extract_exact_around(black_pos, before=16, after=16))
            print()
        else:
            print("     → Stroke黒は見つかりませんでした（Stroke無しファイル）\n")

        # 4C. GradientStop の推定位置
        print(f"[4C] GradientStop の各Stop開始位置（前後32バイト）:")
        stops = self.find_gradient_stops_accurate()
        if stops:
            for stop_num, stop_pos in stops:
                print(f"\n     Stop{stop_num} 開始位置: 0x{stop_pos:04X}\n")
                print(self.extract_exact_around(stop_pos, before=32, after=32))
        else:
            print("     → GradientStop なし（単色Fill）\n")

        print(f"\n{'='*80}\n")


def main():
    # テンプレートファイルのリスト
    templates = [
        "TEMPLATE_SolidFill_White.prtextstyle",
        "TEMPLATE_Grad2_BlueToWhite.prtextstyle",
        "TEMPLATE_Grad3_BlueWhiteRed.prtextstyle",
        "TEMPLATE_SolidFill_White_StrokeBlack.prtextstyle",
        "TEMPLATE_Grad3_BlueWhiteRed_StrokeBlack.prtextstyle",
    ]

    print("\n" + "="*80)
    print("prtextstyle テンプレート Hex Dump 抽出ツール v2")
    print("="*80 + "\n")

    # 解析実行
    for template_name in templates:
        if Path(template_name).exists():
            extractor = TemplateHexExtractorV2(template_name)
            extractor.analyze()
        else:
            print(f"⚠️  {template_name} が見つかりません\n")


if __name__ == "__main__":
    main()
