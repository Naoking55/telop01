#!/usr/bin/env python3
"""
テンプレート .prtextstyle ファイルの詳細 hex dump 抽出ツール - 最終版
- 青・白・Stroke黒の正確な前後16バイト
- GradientStopの前後32バイト（全Stop表示）
"""

import xml.etree.ElementTree as ET
import base64
import zlib
from pathlib import Path
from typing import Optional, List, Tuple


class TemplateHexExtractorFinal:
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
            chunk = self.binary_data[offset:offset+3]
            # RGB(0,0,0)の可能性がある場所を検索
            if chunk == bytes([0x00, 0x00, 0x00]):
                # 前後のコンテキストを確認
                # Stroke色は通常、FF FF FF のような値の後に出現
                if offset > 4:
                    # 有効な候補として返す
                    # ただし、ヘッダの 00 00 00 00 パターンは除外
                    if offset + 3 < len(self.binary_data):
                        next_byte = self.binary_data[offset + 3]
                        # 次のバイトが 0x00 でない場合は有効
                        if next_byte != 0x00 or offset == 0x00BD:
                            return offset

        return None

    def find_all_gradient_stops(self) -> Optional[List[Tuple[int, int]]]:
        """GradientStop の正確な位置を全て検索
        Returns: [(stop_number, offset), ...]
        """
        # 青 (00 00 FF) の全出現位置を検索（0x0200以降）
        blue_positions = []
        search_start = 0x0200

        while True:
            pos = self.find_pattern(bytes([0x00, 0x00, 0xFF]), search_start)
            if not pos:
                break
            blue_positions.append(pos)
            search_start = pos + 1

        if not blue_positions:
            return None

        stops = []

        # 各青色の位置から、GradientStopの開始位置を推定
        for i, blue_pos in enumerate(blue_positions):
            # RGB値の8バイト前がStop開始位置（推定）
            stop_start = blue_pos - 8
            stops.append((i, stop_start))

        return stops if stops else None

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
            print("     → Stroke黒は見つかりませんでした（Stroke無しまたは黒以外の色）\n")

        # 4C. GradientStop の推定位置（全Stop表示）
        print(f"[4C] GradientStop の各Stop開始位置（前後32バイト）:")
        stops = self.find_all_gradient_stops()
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
    print("prtextstyle テンプレート Hex Dump 抽出ツール - 最終版")
    print("="*80 + "\n")

    # 解析実行
    for template_name in templates:
        if Path(template_name).exists():
            extractor = TemplateHexExtractorFinal(template_name)
            extractor.analyze()
        else:
            print(f"⚠️  {template_name} が見つかりません\n")


if __name__ == "__main__":
    main()
