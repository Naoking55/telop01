#!/usr/bin/env python3
"""
GradientStop の 48バイト全体を抽出するツール
"""

import xml.etree.ElementTree as ET
import base64
import zlib
from pathlib import Path
from typing import Optional, List, Tuple


class GradientStopExtractor:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = Path(filepath).name
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
        self.encoded_data: Optional[str] = None
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

        decoded_data = base64.b64decode(self.encoded_data)

        # zlib解凍を試みる
        try:
            self.binary_data = zlib.decompress(decoded_data)
            return self.binary_data
        except zlib.error:
            self.binary_data = decoded_data
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

    def find_all_rgb_patterns(self) -> List[Tuple[str, int]]:
        """全RGB色パターンを検索（0x0200以降のグラデーション領域）"""
        patterns = []
        search_start = 0x0200

        # 青 (00 00 FF) を検索
        offset = search_start
        while True:
            pos = self.binary_data.find(bytes([0x00, 0x00, 0xFF]), offset)
            if pos == -1:
                break
            patterns.append(("青 (00 00 FF)", pos))
            offset = pos + 1

        # 白 (FF FF FF) を検索（0x0200以降）
        offset = search_start
        while True:
            pos = self.binary_data.find(bytes([0xFF, 0xFF, 0xFF]), offset)
            if pos == -1:
                break
            patterns.append(("白 (FF FF FF)", pos))
            offset = pos + 1

        # 赤 (FF 00 00) を検索
        offset = search_start
        while True:
            pos = self.binary_data.find(bytes([0xFF, 0x00, 0x00]), offset)
            if pos == -1:
                break
            patterns.append(("赤 (FF 00 00)", pos))
            offset = pos + 1

        # オフセット順にソート
        patterns.sort(key=lambda x: x[1])
        return patterns

    def find_gradient_stops(self) -> Optional[List[Tuple[int, int]]]:
        """GradientStop の開始位置を検索
        Returns: [(stop_number, start_offset), ...]
        """
        # RGB色パターンを全て検索
        rgb_patterns = self.find_all_rgb_patterns()

        if not rgb_patterns:
            return None

        stops = []

        # 最初のRGB位置から逆算してStop0の開始を推定
        first_rgb_pos = rgb_patterns[0][1]
        stop0_start = first_rgb_pos - 8  # RGB値の8バイト前がStop開始

        stops.append((0, stop0_start))

        # 48バイトごとにStop1, Stop2を計算
        for i in range(1, 4):
            next_stop = stop0_start + (48 * i)
            if next_stop + 48 <= len(self.binary_data):
                stops.append((i, next_stop))
            else:
                break

        return stops

    def analyze(self):
        """完全解析を実行"""
        print(f"{'='*80}")
        print(f"ファイル: {self.filename}")
        print(f"{'='*80}\n")

        # Base64抽出とデコード
        self.extract_base64()
        self.decode_binary()

        print(f"バイナリサイズ: {len(self.binary_data)} bytes\n")

        # グラデーション領域のRGB検索
        print(f"[グラデーション領域のRGB色検出]")
        rgb_patterns = self.find_all_rgb_patterns()
        if rgb_patterns:
            for color_name, offset in rgb_patterns:
                print(f"  {color_name}: 0x{offset:04X}")
            print()
        else:
            print("  → RGB色が見つかりませんでした（単色Fillファイル）\n")
            return

        # GradientStop の 48バイト全体を表示
        print(f"[GradientStop 各 Stop の 48バイト全体]\n")
        stops = self.find_gradient_stops()

        if stops:
            for stop_num, stop_start in stops:
                stop_end = stop_start + 48

                # ファイルサイズを超えないように調整
                if stop_end > len(self.binary_data):
                    stop_end = len(self.binary_data)

                stop_data = self.binary_data[stop_start:stop_end]

                print(f"{'─'*80}")
                print(f"Stop{stop_num} (0x{stop_start:04X} - 0x{stop_end:04X}) [{len(stop_data)} bytes]")
                print(f"{'─'*80}")
                print(self.hex_dump_xxd(stop_data, start_offset=stop_start))
                print()

                # このStop内のRGB値を検出
                print(f"  → Stop{stop_num} 内のRGB値:")
                for color_name, rgb_offset in rgb_patterns:
                    if stop_start <= rgb_offset < stop_end:
                        relative_offset = rgb_offset - stop_start
                        print(f"     {color_name} @ 0x{rgb_offset:04X} (Stop内 +{relative_offset} bytes)")
                print()

        else:
            print("  → GradientStop なし（単色Fill）\n")

        print(f"{'='*80}\n")


def main():
    # グラデーションテンプレートのみ
    templates = [
        "TEMPLATE_Grad2_BlueToWhite.prtextstyle",
        "TEMPLATE_Grad3_BlueWhiteRed.prtextstyle",
        "TEMPLATE_Grad3_BlueWhiteRed_StrokeBlack.prtextstyle",
    ]

    print("\n" + "="*80)
    print("GradientStop 48バイト全体抽出ツール")
    print("="*80 + "\n")

    # 解析実行
    for template_name in templates:
        if Path(template_name).exists():
            extractor = GradientStopExtractor(template_name)
            extractor.analyze()
        else:
            print(f"⚠️  {template_name} が見つかりません\n")


if __name__ == "__main__":
    main()
