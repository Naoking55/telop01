#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
フォントサイズ30と70の完全比較
"""

from xml.etree import ElementTree as ET
import base64
import struct

def extract_binary(filepath: str) -> bytes:
    tree = ET.parse(filepath)
    root = tree.getroot()
    for param in root.findall(".//ArbVideoComponentParam"):
        name_elem = param.find("Name")
        if name_elem is not None and name_elem.text == "ソーステキスト":
            keyframe_val = param.find("StartKeyframeValue")
            if keyframe_val is not None and keyframe_val.text:
                if keyframe_val.attrib.get('Encoding', '') == 'base64':
                    return base64.b64decode(keyframe_val.text.strip())
    return b""

def main():
    print("="*80)
    print("フォントサイズ 30 vs 70 の完全比較")
    print("="*80)

    file_30 = "prtextstyle/青白赤グラ 30.prtextstyle"
    file_70 = "prtextstyle/青白赤グラ 70.prtextstyle"

    bin_30 = extract_binary(file_30)
    bin_70 = extract_binary(file_70)

    print(f"\nサイズ30: {len(bin_30)} bytes")
    print(f"サイズ70: {len(bin_70)} bytes")
    print(f"同一サイズ: {len(bin_30) == len(bin_70)}")

    if len(bin_30) != len(bin_70):
        print("サイズが異なるため比較できません")
        return

    # バイト単位で比較
    print("\n差分箇所:")
    diff_positions = []

    for i in range(len(bin_30)):
        if bin_30[i] != bin_70[i]:
            diff_positions.append(i)

    print(f"総差分バイト数: {len(diff_positions)}")

    # 差分箇所を表示
    print("\n差分の詳細:")

    i = 0
    while i < len(diff_positions):
        start = diff_positions[i]

        # 連続する差分をグループ化
        end = start
        while i + 1 < len(diff_positions) and diff_positions[i + 1] == end + 1:
            i += 1
            end = diff_positions[i]

        i += 1
        length = end - start + 1

        # 周辺を表示
        context_start = max(0, start - 16)
        context_end = min(len(bin_30), end + 32)

        print(f"\n0x{start:04x}-0x{end:04x} ({length} bytes):")

        hex_30 = ' '.join(f'{b:02x}' for b in bin_30[start:end+1])
        hex_70 = ' '.join(f'{b:02x}' for b in bin_70[start:end+1])

        print(f"  30: {hex_30}")
        print(f"  70: {hex_70}")

        # float解釈
        if length >= 4 and start + 4 <= len(bin_30):
            try:
                f_30 = struct.unpack("<f", bin_30[start:start+4])[0]
                f_70 = struct.unpack("<f", bin_70[start:start+4])[0]

                print(f"  Float解釈:")
                print(f"    30: {f_30:.6f}")
                print(f"    70: {f_70:.6f}")

                # フォントサイズらしいか？
                if 25 <= f_30 <= 35 and 65 <= f_70 <= 75:
                    print(f"  ★★★ これがフォントサイズ！ ★★★")

            except:
                pass

        # 整数解釈
        if length >= 4:
            try:
                i_30 = struct.unpack("<I", bin_30[start:start+4])[0]
                i_70 = struct.unpack("<I", bin_70[start:start+4])[0]
                print(f"  UInt32解釈: {i_30} vs {i_70}")
            except:
                pass

        # 周辺コンテキスト
        print(f"\n  周辺 [0x{context_start:04x}-0x{context_end:04x}]:")
        for offset in range(context_start, context_end, 16):
            chunk_30 = bin_30[offset:offset+16]
            chunk_70 = bin_70[offset:offset+16]

            hex_30 = ' '.join(f'{b:02x}' for b in chunk_30)
            hex_70 = ' '.join(f'{b:02x}' for b in chunk_70)

            marker = " <<<" if start <= offset < end + 1 else ""

            print(f"    {offset:04x}:")
            print(f"      30: {hex_30}{marker}")
            print(f"      70: {hex_70}{marker}")

    print("\n" + "="*80)
    print("✅ 比較完了")
    print("="*80)

if __name__ == "__main__":
    main()
