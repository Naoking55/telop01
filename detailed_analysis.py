#!/usr/bin/env python3
"""
詳細なバイナリ解析ツール
特定のオフセットに焦点を当てた解析
"""

import base64
import zlib
import xml.etree.ElementTree as ET
import struct
from pathlib import Path
from typing import List, Tuple


def extract_binary_from_prtextstyle(file_path: str) -> bytes:
    """prtextstyleファイルからバイナリデータを抽出"""
    tree = ET.parse(file_path)
    root = tree.getroot()

    # StartKeyframeValueを探す
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


def parse_float32(data: bytes, offset: int) -> float:
    """指定オフセットからfloat32を読み取る"""
    if offset + 4 <= len(data):
        return struct.unpack('<f', data[offset:offset+4])[0]
    return None


def parse_uint32(data: bytes, offset: int) -> int:
    """指定オフセットからuint32を読み取る"""
    if offset + 4 <= len(data):
        return struct.unpack('<I', data[offset:offset+4])[0]
    return None


def parse_uint8(data: bytes, offset: int) -> int:
    """指定オフセットからuint8を読み取る"""
    if offset < len(data):
        return data[offset]
    return None


def find_color_candidates(data: bytes, skip_zeros: bool = True) -> List[Tuple[int, Tuple[float, float, float, float]]]:
    """連続する4つのfloat32（RGBA候補）を探す"""
    candidates = []
    for i in range(0, len(data) - 15, 1):
        try:
            r = struct.unpack('<f', data[i:i+4])[0]
            g = struct.unpack('<f', data[i+4:i+8])[0]
            b = struct.unpack('<f', data[i+8:i+12])[0]
            a = struct.unpack('<f', data[i+12:i+16])[0]

            # RGBAとして妥当な値（0.0-1.0範囲、またはそれに近い）
            if (-0.1 <= r <= 1.1 and -0.1 <= g <= 1.1 and
                -0.1 <= b <= 1.1 and -0.1 <= a <= 1.1):
                # 全部0はスキップ（オプション）
                if skip_zeros and (r == 0 and g == 0 and b == 0 and a == 0):
                    continue
                # 少なくとも1つの値が0.05以上ある（意味のある値）
                if not skip_zeros or (abs(r) > 0.01 or abs(g) > 0.01 or abs(b) > 0.01 or abs(a) > 0.01):
                    candidates.append((i, (r, g, b, a)))
        except:
            pass
    return candidates


def hex_dump_range(data: bytes, start: int, length: int = 64) -> str:
    """指定範囲をhexダンプ"""
    lines = []
    for i in range(start, min(start + length, len(data)), 16):
        offset = f"{i:08X}"
        chunk = data[i:min(i + 16, len(data))]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        hex_part = hex_part.ljust(47)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{offset}  {hex_part}  |{ascii_part}|")
    return "\n".join(lines)


def compare_and_analyze(files_dict: dict):
    """複数ファイルを比較して解析"""

    print("="*80)
    print("詳細解析レポート")
    print("="*80)
    print()

    # ===== 比較1: 赤 vs 青（単色Fill） =====
    print("### 1. 単色Fill比較: 赤 vs 青 ###")
    print()

    if "赤・ストローク無し.prtextstyle" in files_dict and "青・ストローク無し.prtextstyle" in files_dict:
        red_data = files_dict["赤・ストローク無し.prtextstyle"]
        blue_data = files_dict["青・ストローク無し.prtextstyle"]

        print(f"赤ファイルサイズ: {len(red_data)} bytes")
        print(f"青ファイルサイズ: {len(blue_data)} bytes")
        print()

        # 色候補を探す
        print("【赤】RGBA候補:")
        red_colors = find_color_candidates(red_data)
        for offset, (r, g, b, a) in red_colors[:10]:
            print(f"  0x{offset:04X}: R={r:.4f}, G={g:.4f}, B={b:.4f}, A={a:.4f}")
        print()

        print("【青】RGBA候補:")
        blue_colors = find_color_candidates(blue_data)
        for offset, (r, g, b, a) in blue_colors[:10]:
            print(f"  0x{offset:04X}: R={r:.4f}, G={g:.4f}, B={b:.4f}, A={a:.4f}")
        print()

        # 特定オフセットの詳細比較
        print("【差分分析】")

        # 赤と青で異なる色値を持つオフセットを特定
        for (r_off, r_color), (b_off, b_color) in zip(red_colors, blue_colors):
            if r_off == b_off:
                # 同じオフセットで色が違う場合
                r_r, r_g, r_b, r_a = r_color
                b_r, b_g, b_b, b_a = b_color

                if abs(r_r - b_r) > 0.1 or abs(r_g - b_g) > 0.1 or abs(r_b - b_b) > 0.1:
                    print(f"\n★ 色差分発見: オフセット 0x{r_off:04X}")
                    print(f"  赤: R={r_r:.4f}, G={r_g:.4f}, B={r_b:.4f}, A={r_a:.4f}")
                    print(f"  青: R={b_r:.4f}, G={b_g:.4f}, B={b_b:.4f}, A={b_a:.4f}")
                    print(f"  → Fill.SolidColor の位置と推定")
                    print()
                    print("  コンテキスト（赤）:")
                    print(hex_dump_range(red_data, max(0, r_off - 32), 96))
                    print()
                    print("  コンテキスト（青）:")
                    print(hex_dump_range(blue_data, max(0, b_off - 32), 96))
                    break

    print("\n" + "="*80)
    print("### 2. グラデーション比較: 2色 vs 3色 ###")
    print()

    if "青白グラ・ストローク無し.prtextstyle" in files_dict and "青白赤グラ・ストローク無し.prtextstyle" in files_dict:
        grad2_data = files_dict["青白グラ・ストローク無し.prtextstyle"]
        grad3_data = files_dict["青白赤グラ・ストローク無し.prtextstyle"]

        print(f"2色グラデサイズ: {len(grad2_data)} bytes")
        print(f"3色グラデサイズ: {len(grad3_data)} bytes")
        print(f"サイズ差: {len(grad3_data) - len(grad2_data)} bytes")
        print()

        print("【2色グラデ】RGBA候補:")
        grad2_colors = find_color_candidates(grad2_data)
        for offset, (r, g, b, a) in grad2_colors[:15]:
            print(f"  0x{offset:04X}: R={r:.4f}, G={g:.4f}, B={b:.4f}, A={a:.4f}")
        print()

        print("【3色グラデ】RGBA候補:")
        grad3_colors = find_color_candidates(grad3_data)
        for offset, (r, g, b, a) in grad3_colors[:15]:
            print(f"  0x{offset:04X}: R={r:.4f}, G={g:.4f}, B={b:.4f}, A={a:.4f}")
        print()

    print("\n" + "="*80)
    print("### 3. Stroke比較: 黄エッジ vs 水色エッジ ###")
    print()

    if "白・エッジ黄.prtextstyle" in files_dict and "白・水エッジ.prtextstyle" in files_dict:
        yellow_data = files_dict["白・エッジ黄.prtextstyle"]
        cyan_data = files_dict["白・水エッジ.prtextstyle"]

        print(f"黄エッジサイズ: {len(yellow_data)} bytes")
        print(f"水色エッジサイズ: {len(cyan_data)} bytes")
        print()

        print("【黄エッジ】RGBA候補:")
        yellow_colors = find_color_candidates(yellow_data)
        for offset, (r, g, b, a) in yellow_colors[:10]:
            print(f"  0x{offset:04X}: R={r:.4f}, G={g:.4f}, B={b:.4f}, A={a:.4f}")
        print()

        print("【水色エッジ】RGBA候補:")
        cyan_colors = find_color_candidates(cyan_data)
        for offset, (r, g, b, a) in cyan_colors[:10]:
            print(f"  0x{offset:04X}: R={r:.4f}, G={g:.4f}, B={b:.4f}, A={a:.4f}")
        print()

        # Stroke色の差分を探す
        print("【Stroke色差分分析】")
        for (y_off, y_color), (c_off, c_color) in zip(yellow_colors, cyan_colors):
            if y_off == c_off:
                y_r, y_g, y_b, y_a = y_color
                c_r, c_g, c_b, c_a = c_color

                if abs(y_r - c_r) > 0.1 or abs(y_g - c_g) > 0.1 or abs(y_b - c_b) > 0.1:
                    print(f"\n★ Stroke色差分発見: オフセット 0x{y_off:04X}")
                    print(f"  黄: R={y_r:.4f}, G={y_g:.4f}, B={y_b:.4f}, A={y_a:.4f}")
                    print(f"  水: R={c_r:.4f}, G={c_g:.4f}, B={c_b:.4f}, A={c_a:.4f}")
                    print()
                    print("  コンテキスト（黄）:")
                    print(hex_dump_range(yellow_data, max(0, y_off - 32), 96))
                    print()
                    print("  コンテキスト（水）:")
                    print(hex_dump_range(cyan_data, max(0, c_off - 32), 96))


if __name__ == "__main__":
    # すべてのファイルを読み込み
    prtextstyle_files = sorted(Path(".").glob("*.prtextstyle"))

    files_dict = {}
    for file_path in prtextstyle_files:
        binary_data = extract_binary_from_prtextstyle(str(file_path))
        if binary_data:
            files_dict[file_path.name] = binary_data
            print(f"✓ 読み込み: {file_path.name} ({len(binary_data)} bytes)")

    print()
    compare_and_analyze(files_dict)
