#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlatBuffers形式の解析
"""

from xml.etree import ElementTree as ET
import base64
import struct
import sys

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

def read_i32(data: bytes, offset: int) -> int:
    """32bit signed integer (little-endian)"""
    return struct.unpack("<i", data[offset:offset+4])[0]

def read_u32(data: bytes, offset: int) -> int:
    """32bit unsigned integer (little-endian)"""
    return struct.unpack("<I", data[offset:offset+4])[0]

def read_f32(data: bytes, offset: int) -> float:
    """32bit float (little-endian)"""
    return struct.unpack("<f", data[offset:offset+4])[0]

def analyze_flatbuffers(binary: bytes, name: str):
    """FlatBuffers構造を解析"""
    print(f"\n{'='*80}")
    print(f"{name} - FlatBuffers解析")
    print(f"{'='*80}")
    print(f"サイズ: {len(binary)} bytes")

    # 最初の4バイト：ルートテーブルへのオフセット
    root_offset = read_u32(binary, 0)
    print(f"\nルートテーブルオフセット: 0x{root_offset:04x} ({root_offset})")

    # オフセット 0x0008: マジックナンバー
    if len(binary) >= 12:
        magic = binary[8:12]
        print(f"マジックナンバー: {magic.hex()} ({magic})")

    # vtableの解析
    print("\n[VTable構造の推定]")
    vtable_start = 0x00b0
    print(f"VTable候補位置: 0x{vtable_start:04x}")

    for i in range(vtable_start, min(vtable_start + 64, len(binary)), 4):
        val = read_i32(binary, i)
        if val == -1:
            print(f"  0x{i:04x}: -1 (null)")
        elif -1000 < val < 1000 and val != 0:
            print(f"  0x{i:04x}: {val} (offset?)")
        elif val != 0:
            # floatとして解釈してみる
            f = read_f32(binary, i)
            if -1.0 <= f <= 1.0:
                print(f"  0x{i:04x}: 0x{val:08x} (float: {f:.6f})")
            else:
                print(f"  0x{i:04x}: 0x{val:08x}")

    # テーブルデータの解析
    print("\n[テーブルデータの推定]")

    # 0x0140-0x0160 付近に数値データがありそう
    interesting_offsets = [0x0140, 0x0150, 0x0160, 0x0170, 0x0180, 0x0190]

    for offset in interesting_offsets:
        if offset + 16 <= len(binary):
            # 整数として
            i1 = read_u32(binary, offset)
            i2 = read_u32(binary, offset + 4)
            i3 = read_u32(binary, offset + 8)

            # floatとして
            f1 = read_f32(binary, offset)
            f2 = read_f32(binary, offset + 4)
            f3 = read_f32(binary, offset + 8)
            f4 = read_f32(binary, offset + 12)

            print(f"\n0x{offset:04x}:")
            print(f"  整数: {i1}, {i2}, {i3}")
            if -1.0 <= f1 <= 100.0 and -1.0 <= f2 <= 100.0:
                print(f"  float: {f1:.6f}, {f2:.6f}, {f3:.6f}, {f4:.6f}")

            # 16進数ダンプ
            chunk = binary[offset:offset+16]
            print(f"  hex: {chunk.hex()}")

def compare_color_areas(binaries: dict):
    """色データがありそうな領域を比較"""
    print("\n" + "="*80)
    print("色データ候補領域の比較")
    print("="*80)

    # 各領域を検査
    areas = [
        (0x0140, 16, "0x0140-0x0150"),
        (0x0150, 16, "0x0150-0x0160"),
        (0x0160, 16, "0x0160-0x0170"),
        (0x0190, 16, "0x0190-0x01a0"),
    ]

    for offset, length, label in areas:
        print(f"\n[{label}]")

        for name in ["White", "Red", "Blue"]:
            if name not in binaries:
                continue

            binary = binaries[name]
            if offset + length > len(binary):
                continue

            chunk = binary[offset:offset+length]
            hex_str = chunk.hex()

            # floatとして解釈
            try:
                floats = []
                for i in range(0, length, 4):
                    if i + 4 <= length:
                        f = struct.unpack("<f", chunk[i:i+4])[0]
                        floats.append(f)

                # 整数としても解釈
                ints = []
                for i in range(0, length, 4):
                    if i + 4 <= length:
                        val = struct.unpack("<I", chunk[i:i+4])[0]
                        ints.append(val)

                print(f"{name:12s}: {hex_str}")
                print(f"              int: {ints}")
                print(f"              flt: {[f'{f:.3f}' for f in floats]}")

            except:
                print(f"{name:12s}: {hex_str}")

def main():
    print("="*80)
    print("FlatBuffers バイナリフォーマット解析")
    print("="*80)

    # ファイル読み込み
    files = {
        "White": "TEMPLATE_SolidFill_White.prtextstyle",
        "Red": "赤・ストローク無し.prtextstyle",
        "Blue": "青・ストローク無し.prtextstyle",
    }

    binaries = {}
    for name, filepath in files.items():
        try:
            binary = extract_binary(filepath)
            if binary:
                binaries[name] = binary
                print(f"✓ {name}: {len(binary)} bytes")
        except Exception as e:
            print(f"✗ {name}: エラー - {e}")

    if not binaries:
        print("バイナリデータが見つかりませんでした")
        return

    # 各ファイルの構造解析
    for name, binary in binaries.items():
        analyze_flatbuffers(binary, name)

    # 色データ領域の比較
    compare_color_areas(binaries)

    # 最終結論
    print("\n\n" + "="*80)
    print("解析結果のまとめ")
    print("="*80)

    print("""
FlatBuffers形式と判明:
- 0x0000-0x0003: ルートテーブルへのオフセット
- 0x0008-0x000b: マジックナンバー "D3\\"\\x11"
- 0x00b0-0x00c0: VTable（オフセットテーブル）
- 0x00d0付近: フォント名文字列 ("VD-LogoG-Extra-G")
- 0x0140-0x0150: サイズ関連のデータ
- 0x0150-0x0180: 色データの可能性が高い領域

次のステップ:
1. FlatBuffers schemaを推定
2. 正確なフィールド位置を特定
3. エンコーダーを実装
""")

    print("\n" + "="*80)
    print("✅ 解析完了")
    print("="*80)

if __name__ == "__main__":
    main()
