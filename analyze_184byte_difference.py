#!/usr/bin/env python3
"""
Fontstyle_01（732バイト） vs Fontstyle_11（916バイト）の184バイト差分を詳細解析

同じRGBA色を持つが、サイズが異なる2つのスタイルを比較し、
追加データ（ストローク/シャドウ）の構造を理解する
"""

import xml.etree.ElementTree as ET
import base64
import struct

def get_style_binary(filepath, style_name):
    """スタイルのバイナリデータを取得"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    for style_item in root.findall('.//StyleProjectItem'):
        name_elem = style_item.find('.//Name')
        if name_elem is not None and name_elem.text == style_name:
            component_ref_elem = style_item.find('.//Component[@ObjectRef]')
            component_ref = component_ref_elem.get('ObjectRef')
            vfc = root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")
            first_param_ref = vfc.find(".//Param[@Index='0']")
            param_obj_ref = first_param_ref.get('ObjectRef')
            arb_param = root.find(f".//ArbVideoComponentParam[@ObjectID='{param_obj_ref}']")
            binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
            return base64.b64decode(binary_elem.text.strip())
    return None

def hex_dump(data, start=0, length=256, title="", highlight_ranges=None):
    """16進ダンプ（範囲ハイライト対応）"""
    highlight_ranges = highlight_ranges or []

    if title:
        print(f"\n{title}")
        print("-" * 80)

    for i in range(start, min(start + length, len(data)), 16):
        offset_str = f"{i:04x}"

        hex_parts = []
        for j in range(16):
            if i + j < len(data):
                byte = data[i + j]
                # ハイライト判定
                is_highlighted = any(start <= i + j < end for start, end in highlight_ranges)
                if is_highlighted:
                    hex_parts.append(f"\033[93m{byte:02x}\033[0m")  # 黄色
                else:
                    hex_parts.append(f"{byte:02x}")
            else:
                hex_parts.append("  ")

        hex_str = " ".join(hex_parts[:8]) + "  " + " ".join(hex_parts[8:])

        ascii_parts = []
        for j in range(16):
            if i + j < len(data):
                byte = data[i + j]
                if 32 <= byte < 127:
                    ascii_parts.append(chr(byte))
                else:
                    ascii_parts.append(".")
            else:
                ascii_parts.append(" ")

        ascii_str = "".join(ascii_parts)
        print(f"{offset_str}  {hex_str}  |{ascii_str}|")

def find_differences(bin1, bin2):
    """2つのバイナリの差分領域を検出"""
    min_len = min(len(bin1), len(bin2))
    differences = []

    i = 0
    while i < min_len:
        if bin1[i] != bin2[i]:
            start = i
            while i < min_len and bin1[i] != bin2[i]:
                i += 1
            differences.append((start, i))
        else:
            i += 1

    return differences

def find_common_sequences(bin1, bin2, min_length=16):
    """共通のバイトシーケンスを検出"""
    common_seqs = []
    i = 0

    while i < min(len(bin1), len(bin2)):
        if bin1[i] == bin2[i]:
            start = i
            length = 0
            while i < min(len(bin1), len(bin2)) and bin1[i] == bin2[i]:
                length += 1
                i += 1
            if length >= min_length:
                common_seqs.append((start, start + length, length))
        else:
            i += 1

    return common_seqs

def analyze_extra_data(bin_small, bin_large):
    """追加データの位置を特定"""
    print(f"\n{'='*80}")
    print("追加データの位置特定")
    print(f"{'='*80}\n")

    # 共通シーケンスを検出
    common_seqs = find_common_sequences(bin_small, bin_large, min_length=32)

    print(f"共通シーケンス（32バイト以上）: {len(common_seqs)} 個\n")

    # 追加データの領域を推定
    if common_seqs:
        print("共通領域マップ:")
        for i, (start, end, length) in enumerate(common_seqs[:10], 1):
            print(f"  {i}. 0x{start:04x} - 0x{end:04x} ({length} bytes)")

        # 最初の大きな共通領域の後に追加データがあると仮定
        if len(common_seqs) > 0:
            first_common_end = common_seqs[0][1]

            print(f"\n推定: 0x{first_common_end:04x} 付近に追加データが挿入されている可能性")

            # その付近を比較
            return first_common_end

    return None

def compare_side_by_side(bin1, bin2, offset, context=64):
    """2つのバイナリを並べて比較"""
    print(f"\n{'='*80}")
    print(f"0x{offset:04x} 付近の比較（前後{context}バイト）")
    print(f"{'='*80}\n")

    start = max(0, offset - context)
    end = min(len(bin1), offset + context)

    print("Fontstyle_01 (732バイト):")
    hex_dump(bin1, start, end - start)

    print(f"\nFontstyle_11 (916バイト) - 同じ領域:")
    hex_dump(bin2, start, min(end - start, len(bin2) - start))

def interpret_as_floats(data, start, count=16):
    """バイト列をfloat値として解釈"""
    print(f"\n0x{start:04x} からの float 値:")
    for i in range(count):
        offset = start + (i * 4)
        if offset + 4 <= len(data):
            try:
                value = struct.unpack("<f", data[offset:offset+4])[0]
                print(f"  0x{offset:04x}: {value:12.6f}")
            except:
                pass

def main():
    filepath = "prtextstyle/100 New Fonstyle.prtextstyle"

    # 2つのスタイルを取得
    bin_01 = get_style_binary(filepath, "Fontstyle_01")
    bin_11 = get_style_binary(filepath, "Fontstyle_11")

    if not bin_01 or not bin_11:
        print("❌ スタイルの取得に失敗")
        return

    print(f"{'='*80}")
    print(f"Fontstyle_01 vs Fontstyle_11 詳細比較")
    print(f"{'='*80}\n")

    print(f"Fontstyle_01: {len(bin_01)} bytes")
    print(f"Fontstyle_11: {len(bin_11)} bytes")
    print(f"差分: {len(bin_11) - len(bin_01)} bytes\n")

    # RGBA色の確認
    print("RGBA色の確認:")
    r1, g1, b1, a1 = bin_01[0x214:0x218]
    r11, g11, b11, a11 = bin_11[0x2aa:0x2ae]
    print(f"  Fontstyle_01 (0x0214): R={r1:3d} G={g1:3d} B={b1:3d} A={a1:3d}")
    print(f"  Fontstyle_11 (0x02aa): R={r11:3d} G={g11:3d} B={b11:3d} A={a11:3d}")
    print(f"  → 同じ色！" if (r1, g1, b1, a1) == (r11, g11, b11, a11) else "  → 異なる色")

    # 差分領域を検出
    print(f"\n{'='*80}")
    print("バイト単位の差分検出")
    print(f"{'='*80}\n")

    differences = find_differences(bin_01, bin_11)
    print(f"差分領域: {len(differences)} 個\n")

    total_diff_bytes = sum(end - start for start, end in differences)
    print(f"差分バイト総数: {total_diff_bytes} / {min(len(bin_01), len(bin_11))}")
    print(f"一致率: {100 - (total_diff_bytes * 100 // min(len(bin_01), len(bin_11)))}%\n")

    print("差分領域（最初の15個）:")
    for i, (start, end) in enumerate(differences[:15], 1):
        length = end - start
        print(f"  {i:2d}. 0x{start:04x} - 0x{end:04x} ({length:3d} bytes)")

    # 追加データの位置を特定
    insertion_point = analyze_extra_data(bin_01, bin_11)

    # ヘッダー部分を比較
    print(f"\n{'='*80}")
    print("ヘッダー部分の比較 (0x0000-0x0040)")
    print(f"{'='*80}\n")

    print("Fontstyle_01:")
    hex_dump(bin_01, 0, 64)

    print("\nFontstyle_11:")
    hex_dump(bin_11, 0, 64)

    # 最初の大きな差分領域を詳しく見る
    if differences:
        first_large_diff = None
        for start, end in differences:
            if end - start > 50:
                first_large_diff = (start, end)
                break

        if first_large_diff:
            start, end = first_large_diff
            print(f"\n{'='*80}")
            print(f"最初の大きな差分領域: 0x{start:04x} - 0x{end:04x} ({end-start} bytes)")
            print(f"{'='*80}\n")

            print("Fontstyle_01:")
            hex_dump(bin_01, max(0, start-16), min(96, end - start + 32))

            print("\nFontstyle_11:")
            hex_dump(bin_11, max(0, start-16), min(96, end - start + 32))

            # この領域をfloatとして解釈
            interpret_as_floats(bin_11, start, 16)

    # サイズ差による追加データ
    if len(bin_11) > len(bin_01):
        print(f"\n{'='*80}")
        print(f"追加データ領域（末尾から逆算）")
        print(f"{'='*80}\n")

        # 末尾から184バイト前
        extra_start = len(bin_01)
        print(f"Fontstyle_11 の 0x{extra_start:04x} 以降 (追加された領域):")
        hex_dump(bin_11, extra_start, min(256, len(bin_11) - extra_start))

    # ファイル末尾の比較
    print(f"\n{'='*80}")
    print("ファイル末尾の比較（最後の64バイト）")
    print(f"{'='*80}\n")

    print("Fontstyle_01:")
    hex_dump(bin_01, len(bin_01) - 64, 64)

    print("\nFontstyle_11:")
    hex_dump(bin_11, len(bin_11) - 64, 64)

if __name__ == "__main__":
    main()
