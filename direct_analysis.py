#!/usr/bin/env python3
"""
直接的なバイナリ解析 - 特定オフセットに焦点を当てる
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


def hex_dump(data: bytes, start: int = 0, length: int = None):
    """Hexダンプ"""
    if length is None:
        length = len(data)
    end = min(start + length, len(data))

    for i in range(start, end, 16):
        offset = f"{i:08X}"
        chunk = data[i:min(i + 16, len(data))]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        hex_part = hex_part.ljust(47)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{offset}  {hex_part}  |{ascii_part}|")


def read_float32(data: bytes, offset: int) -> float:
    """Float32を読み取る（リトルエンディアン）"""
    if offset + 4 <= len(data):
        return struct.unpack('<f', data[offset:offset+4])[0]
    return None


def read_uint32(data: bytes, offset: int) -> int:
    """Uint32を読み取る"""
    if offset + 4 <= len(data):
        return struct.unpack('<I', data[offset:offset+4])[0]
    return None


def read_uint8(data: bytes, offset: int) -> int:
    """Uint8を読み取る"""
    if offset < len(data):
        return data[offset]
    return None


def scan_for_floats_in_range(data: bytes, min_val: float = 0.0, max_val: float = 1.0):
    """特定範囲のfloat値を全走査"""
    print(f"Float32値スキャン（範囲: {min_val} - {max_val}）:")
    print()

    count = 0
    for i in range(0, len(data) - 3):
        try:
            val = struct.unpack('<f', data[i:i+4])[0]
            if min_val <= val <= max_val and abs(val) > 0.01:  # 0に近い値は除外
                print(f"  0x{i:04X} ({i:4d}): {val:.6f}")
                count += 1
                if count >= 30:  # 最初の30個まで
                    break
        except:
            pass


def analyze_specific_offsets(name: str, data: bytes, interesting_offsets: list):
    """特定オフセットの値を詳細に調べる"""
    print(f"\n【{name}】")
    print(f"サイズ: {len(data)} bytes")
    print()

    for offset in interesting_offsets:
        if offset + 16 <= len(data):
            # 4つのfloat32として読む（RGBA候補）
            r = read_float32(data, offset)
            g = read_float32(data, offset + 4)
            b = read_float32(data, offset + 8)
            a = read_float32(data, offset + 12)

            print(f"オフセット 0x{offset:04X}:")
            print(f"  Float32 x4: R={r:.6f}, G={g:.6f}, B={b:.6f}, A={a:.6f}")

            # Hex表示
            chunk = data[offset:offset+16]
            hex_str = " ".join(f"{b:02X}" for b in chunk)
            print(f"  Hex: {hex_str}")
            print()


def compare_byte_by_byte(name1: str, data1: bytes, name2: str, data2: bytes):
    """バイト単位で比較"""
    print(f"\n{'='*80}")
    print(f"差分比較: {name1} vs {name2}")
    print(f"{'='*80}\n")

    min_len = min(len(data1), len(data2))

    diffs = []
    i = 0
    while i < min_len:
        if data1[i] != data2[i]:
            # 差分の開始
            start = i
            while i < min_len and data1[i] != data2[i]:
                i += 1
            end = i
            diffs.append((start, end))
        else:
            i += 1

    print(f"差分箇所数: {len(diffs)}")
    print()

    # 4バイト以上の差分を表示（float値の可能性）
    for idx, (start, end) in enumerate(diffs):
        length = end - start
        if length >= 4:  # 4バイト以上の差分に注目
            print(f"差分 #{idx+1}: オフセット 0x{start:04X} - 0x{end:04X} ({length} bytes)")

            # Float32として解釈してみる
            if length == 4:
                val1 = read_float32(data1, start)
                val2 = read_float32(data2, start)
                print(f"  Float32解釈: {val1:.6f} → {val2:.6f}")

            elif length >= 16 and length % 4 == 0:
                # 複数のfloat32
                print(f"  {name1}:")
                for j in range(0, min(length, 16), 4):
                    val = read_float32(data1, start + j)
                    print(f"    +{j:02X}: {val:.6f}")

                print(f"  {name2}:")
                for j in range(0, min(length, 16), 4):
                    val = read_float32(data2, start + j)
                    print(f"    +{j:02X}: {val:.6f}")

            # Hex表示
            print(f"  Hex ({name1}):")
            chunk1 = data1[start:end]
            for j in range(0, len(chunk1), 16):
                sub = chunk1[j:j+16]
                hex_str = " ".join(f"{b:02X}" for b in sub)
                print(f"    {hex_str}")

            print(f"  Hex ({name2}):")
            chunk2 = data2[start:min(end, len(data2))]
            for j in range(0, len(chunk2), 16):
                sub = chunk2[j:j+16]
                hex_str = " ".join(f"{b:02X}" for b in sub)
                print(f"    {hex_str}")

            print()

        if idx >= 20:  # 最初の20個まで
            print(f"（残り {len(diffs) - 20} 個は省略）")
            break


if __name__ == "__main__":
    print("="*80)
    print("prtextstyle バイナリ構造解析")
    print("="*80)
    print()

    # ファイル読み込み
    files = {
        "赤・ストローク無し": "赤・ストローク無し.prtextstyle",
        "青・ストローク無し": "青・ストローク無し.prtextstyle",
        "青白グラ・ストローク無し": "青白グラ・ストローク無し.prtextstyle",
        "青白赤グラ・ストローク無し": "青白赤グラ・ストローク無し.prtextstyle",
        "白・エッジ黄": "白・エッジ黄.prtextstyle",
        "白・水エッジ": "白・水エッジ.prtextstyle",
    }

    data_dict = {}
    for name, filepath in files.items():
        if Path(filepath).exists():
            data = extract_binary_from_prtextstyle(filepath)
            if data:
                data_dict[name] = data
                print(f"✓ {name}: {len(data)} bytes")

    print()

    # === 比較1: 赤 vs 青（単色Fill） ===
    if "赤・ストローク無し" in data_dict and "青・ストローク無し" in data_dict:
        compare_byte_by_byte(
            "赤・ストローク無し",
            data_dict["赤・ストローク無し"],
            "青・ストローク無し",
            data_dict["青・ストローク無し"]
        )

    # === 比較2: 2色グラデ vs 3色グラデ ===
    if "青白グラ・ストローク無し" in data_dict and "青白赤グラ・ストローク無し" in data_dict:
        compare_byte_by_byte(
            "青白グラ・ストローク無し",
            data_dict["青白グラ・ストローク無し"],
            "青白赤グラ・ストローク無し",
            data_dict["青白赤グラ・ストローク無し"]
        )

    # === 比較3: 黄ストローク vs 水色ストローク ===
    if "白・エッジ黄" in data_dict and "白・水エッジ" in data_dict:
        compare_byte_by_byte(
            "白・エッジ黄",
            data_dict["白・エッジ黄"],
            "白・水エッジ",
            data_dict["白・水エッジ"]
        )

    # === 追加: 特定オフセットの詳細調査 ===
    print("\n" + "="*80)
    print("特定オフセット調査（推測される色情報の位置）")
    print("="*80)

    # 赤のhexダンプで 0x0150付近に EF 55 B6 40 という値が見えた
    interesting_offsets = [0x014C, 0x0150, 0x0154, 0x0158, 0x015C, 0x0160, 0x0164, 0x0168]

    if "赤・ストローク無し" in data_dict:
        analyze_specific_offsets("赤・ストローク無し", data_dict["赤・ストローク無し"], interesting_offsets)

    if "青・ストローク無し" in data_dict:
        analyze_specific_offsets("青・ストローク無し", data_dict["青・ストローク無し"], interesting_offsets)
