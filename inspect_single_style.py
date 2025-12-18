#!/usr/bin/env python3
"""
単一スタイルのバイナリを詳細調査
"""

import xml.etree.ElementTree as ET
import base64
import struct
import sys

def hex_dump(data, start=0, length=256, highlight_offsets=None):
    """16進ダンプ"""
    highlight_offsets = highlight_offsets or []

    for i in range(start, min(start + length, len(data)), 16):
        # オフセット
        offset_str = f"{i:04x}"

        # 16進数
        hex_parts = []
        for j in range(16):
            if i + j < len(data):
                byte = data[i + j]
                if i + j in highlight_offsets:
                    hex_parts.append(f"\033[91m{byte:02x}\033[0m")  # 赤でハイライト
                else:
                    hex_parts.append(f"{byte:02x}")
            else:
                hex_parts.append("  ")

        hex_str = " ".join(hex_parts[:8]) + "  " + " ".join(hex_parts[8:])

        # ASCII
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

def search_strings(data, min_length=3):
    """ASCII文字列を検索"""
    strings = []
    current_string = []
    start_offset = 0

    for i, byte in enumerate(data):
        if 32 <= byte < 127:  # 印字可能なASCII
            if not current_string:
                start_offset = i
            current_string.append(chr(byte))
        else:
            if len(current_string) >= min_length:
                strings.append((start_offset, "".join(current_string)))
            current_string = []

    if len(current_string) >= min_length:
        strings.append((start_offset, "".join(current_string)))

    return strings

def interpret_float(data, offset):
    """float32として解釈"""
    if offset + 4 <= len(data):
        return struct.unpack("<f", data[offset:offset+4])[0]
    return None

def main():
    filepath = "prtextstyle/100 New Fonstyle.prtextstyle"

    tree = ET.parse(filepath)
    root = tree.getroot()

    # 最初のスタイルのバイナリを取得
    style_item = root.find('.//StyleProjectItem')
    name_elem = style_item.find('.//Name')
    style_name = name_elem.text if name_elem is not None else "Unknown"

    component_ref_elem = style_item.find('.//Component[@ObjectRef]')
    component_ref = component_ref_elem.get('ObjectRef')

    vfc = root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")
    first_param_ref = vfc.find(".//Param[@Index='0']")
    param_obj_ref = first_param_ref.get('ObjectRef')

    arb_param = root.find(f".//ArbVideoComponentParam[@ObjectID='{param_obj_ref}']")
    binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")

    binary_data = base64.b64decode(binary_elem.text.strip())

    print(f"{'='*80}")
    print(f"スタイル: {style_name}")
    print(f"バイナリサイズ: {len(binary_data)} bytes")
    print(f"{'='*80}\n")

    # マジックナンバー確認
    print("🔍 ヘッダー領域 (0x0000-0x0020):")
    hex_dump(binary_data, 0, 32)

    # 文字列検索
    print(f"\n\n📝 検出された文字列 (3文字以上):")
    strings = search_strings(binary_data)
    for offset, string in strings[:20]:
        print(f"  0x{offset:04x}: {string}")

    # 0x009c付近のfloat値
    print(f"\n\n🔢 0x0090-0x00b0 のfloat値:")
    for offset in range(0x90, min(0xb0, len(binary_data) - 4), 4):
        value = interpret_float(binary_data, offset)
        if value is not None:
            print(f"  0x{offset:04x}: {value:12.6f}")

    # 0x00c0付近（フォント名エリア）
    print(f"\n\n📄 0x00c0-0x0120 (フォント名エリア?):")
    hex_dump(binary_data, 0xc0, 96)

    # サンプルテキスト "Aa" を探す
    aa_pos = binary_data.find(b'Aa')
    if aa_pos >= 0:
        print(f"\n\n💡 'Aa' 発見: 0x{aa_pos:04x}")
        print(f"周辺:")
        hex_dump(binary_data, max(0, aa_pos - 32), 64, [aa_pos, aa_pos + 1])

    # ファイル末尾
    print(f"\n\n📌 ファイル末尾 (最後の64バイト):")
    hex_dump(binary_data, len(binary_data) - 64, 64)

    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()
