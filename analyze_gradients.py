#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
グラデーションファイルを解析して色データの位置を特定
"""

from xml.etree import ElementTree as ET
import base64
import struct

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

def find_color_candidates(binary: bytes) -> list:
    """色候補を探す（4連続floatで全て0.0-1.0の範囲）"""
    candidates = []

    for i in range(0, len(binary) - 15, 1):
        try:
            r, g, b, a = struct.unpack("<ffff", binary[i:i+16])

            # 全て0.0-1.0の範囲
            if all(0.0 <= v <= 1.0 for v in [r, g, b, a]):
                # 全て0.0は除外
                if not all(v == 0.0 for v in [r, g, b, a]):
                    # アルファが1.0付近か、少なくとも1つの色成分が0でない
                    if a >= 0.9 or any(v > 0.01 for v in [r, g, b]):
                        candidates.append((i, r, g, b, a))
        except:
            pass

    return candidates

def hex_dump_region(binary: bytes, start: int, length: int) -> str:
    """指定領域をhexダンプ"""
    lines = []
    for i in range(start, min(start + length, len(binary)), 16):
        chunk = binary[i:i+16]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"{i:04x}:  {hex_part:<48}  {ascii_part}")
    return '\n'.join(lines)

def main():
    print("="*80)
    print("グラデーションファイルの解析")
    print("="*80)

    # グラデーションファイル
    files = {
        "BlueWhite": "TEMPLATE_Grad2_BlueToWhite.prtextstyle",
        "BlueWhiteRed": "TEMPLATE_Grad3_BlueWhiteRed.prtextstyle",
        "White": "TEMPLATE_SolidFill_White.prtextstyle",
        "Red": "赤・ストローク無し.prtextstyle",
    }

    binaries = {}
    for name, filepath in files.items():
        try:
            binary = extract_binary(filepath)
            if binary:
                binaries[name] = binary
                print(f"✓ {name}: {len(binary)} bytes")
        except Exception as e:
            print(f"✗ {name}: {e}")

    if not binaries:
        print("バイナリデータが見つかりませんでした")
        return

    # 色候補を探す
    print("\n" + "="*80)
    print("色候補（RGBA float 0.0-1.0）の検索")
    print("="*80)

    for name, binary in binaries.items():
        candidates = find_color_candidates(binary)

        print(f"\n[{name}]")
        print(f"候補数: {len(candidates)}")

        for offset, r, g, b, a in candidates[:10]:  # 最初の10個
            print(f"  0x{offset:04x}: R={r:.3f}, G={g:.3f}, B={b:.3f}, A={a:.3f}")

            # 周辺のデータも表示
            if offset >= 16:
                context_start = offset - 16
                context_end = offset + 32
                print(f"    周辺データ:")
                for line in hex_dump_region(binary, context_start, context_end - context_start).split('\n'):
                    print(f"      {line}")

    # グラデーションファイル特有のパターンを探す
    print("\n\n" + "="*80)
    print("グラデーションファイル特有のデータ構造")
    print("="*80)

    if "BlueWhite" in binaries and "White" in binaries:
        blue_white_grad = binaries["BlueWhite"]
        white_solid = binaries["White"]

        print(f"\nBlueWhiteグラデーション: {len(blue_white_grad)} bytes")
        print(f"White単色: {len(white_solid)} bytes")
        print(f"差分: {len(blue_white_grad) - len(white_solid)} bytes")

        # サイズの違いから、グラデーションには追加データがあることがわかる

        # 最初の512バイトを比較
        print("\n最初の512バイトの比較:")
        print("\n[BlueWhite グラデーション]")
        print(hex_dump_region(blue_white_grad, 0, 512))

    # 3色グラデーション
    if "BlueWhiteRed" in binaries:
        blue_white_red = binaries["BlueWhiteRed"]

        print("\n\n" + "="*80)
        print("3色グラデーション (Blue-White-Red)")
        print("="*80)
        print(f"サイズ: {len(blue_white_red)} bytes")

        print("\n最初の512バイトの比較:")
        print(hex_dump_region(blue_white_red, 0, 512))

        # 色候補
        candidates = find_color_candidates(blue_white_red)
        print(f"\n\n色候補: {len(candidates)}個")
        for offset, r, g, b, a in candidates:
            color_desc = ""
            if r > 0.9 and g < 0.1 and b < 0.1:
                color_desc = " ← 赤？"
            elif r < 0.1 and g < 0.1 and b > 0.9:
                color_desc = " ← 青？"
            elif r > 0.9 and g > 0.9 and b > 0.9:
                color_desc = " ← 白？"

            print(f"  0x{offset:04x}: R={r:.3f}, G={g:.3f}, B={b:.3f}, A={a:.3f}{color_desc}")

    print("\n" + "="*80)
    print("✅ 解析完了")
    print("="*80)

if __name__ == "__main__":
    main()
