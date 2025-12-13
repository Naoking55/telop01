#!/usr/bin/env python3
"""
PRSL → prtextstyle 変換ツール（修正版）
既存のprtextstyleファイルをベースに、PRSLパラメータを適用
"""

import os
import sys
import struct
import xml.etree.ElementTree as ET
import base64
import math
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# 既存のPRSLパーサーを再利用
from test_prsl_conversion import parse_prsl, Style


class PrtextstyleConverter:
    """既存prtextstyleファイルベースのコンバーター"""

    def __init__(self, base_filepath: str = "prtextstyle/100 New Fonstyle.prtextstyle"):
        """
        Args:
            base_filepath: ベースとなるprtextstyleファイル
        """
        self.base_filepath = base_filepath
        self.tree = None
        self.root = None
        self.base_style = None
        self._load_base()

    def _load_base(self):
        """ベースファイルを読み込み"""
        if not os.path.exists(self.base_filepath):
            raise FileNotFoundError(f"Base file not found: {self.base_filepath}")

        self.tree = ET.parse(self.base_filepath)
        self.root = self.tree.getroot()

        # 最初のスタイルをテンプレートとして使用
        for style_item in self.root.findall('.//StyleProjectItem'):
            self.base_style = style_item
            break

        if self.base_style is None:
            raise ValueError("No style found in base file")

        print(f"✓ Loaded base file: {self.base_filepath}")

    def _get_style_binary(self, style_item):
        """StyleProjectItemからバイナリデータを取得"""
        component_ref_elem = style_item.find('.//Component[@ObjectRef]')
        if component_ref_elem is None:
            return None

        component_ref = component_ref_elem.get('ObjectRef')
        vfc = self.root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")
        if vfc is None:
            return None

        first_param_ref = vfc.find(".//Param[@Index='0']")
        if first_param_ref is None:
            return None

        param_obj_ref = first_param_ref.get('ObjectRef')
        arb_param = self.root.find(f".//ArbVideoComponentParam[@ObjectID='{param_obj_ref}']")
        if arb_param is None:
            return None

        binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
        if binary_elem is None or not binary_elem.text:
            return None

        return base64.b64decode(binary_elem.text.strip()), binary_elem

    def _apply_fill_color(self, binary: bytearray, style: Style) -> bytearray:
        """Fill色を適用"""
        if style.fill.is_gradient():
            return binary  # グラデーションは未対応

        # RGBA float (0.0-1.0) を探す
        target_r = style.fill.r / 255.0
        target_g = style.fill.g / 255.0
        target_b = style.fill.b / 255.0
        target_a = style.fill.a / 255.0

        # 全体をスキャンして、妥当なRGBA位置を探す
        for offset in range(0, len(binary) - 15, 4):
            try:
                r = struct.unpack('<f', binary[offset:offset+4])[0]
                g = struct.unpack('<f', binary[offset+4:offset+8])[0]
                b = struct.unpack('<f', binary[offset+8:offset+12])[0]
                a = struct.unpack('<f', binary[offset+12:offset+16])[0]

                # 有効なRGBA (全て0.0-1.0、Alphaが0でない)
                if all(0.0 <= v <= 1.0 for v in [r, g, b, a]) and a > 0.01:
                    # 最初に見つけたRGBAを置き換え
                    struct.pack_into('<f', binary, offset, target_r)
                    struct.pack_into('<f', binary, offset + 4, target_g)
                    struct.pack_into('<f', binary, offset + 8, target_b)
                    struct.pack_into('<f', binary, offset + 12, target_a)
                    print(f"  Fill色を適用: RGB({style.fill.r}, {style.fill.g}, {style.fill.b}) @ 0x{offset:04x}")
                    return binary  # 最初の1つだけ変更
            except:
                pass

        print(f"  ⚠️ Fill色の適用位置が見つかりませんでした")
        return binary

    def _apply_shadow(self, binary: bytearray, style: Style) -> bytearray:
        """シャドウを適用"""
        if not style.shadow.enabled:
            return binary

        # Shadow X,Yペアを探す
        for offset in range(0, len(binary) - 7, 4):
            try:
                x = struct.unpack('<f', binary[offset:offset+4])[0]
                y = struct.unpack('<f', binary[offset+4:offset+8])[0]

                # 妥当なShadow offset範囲
                if -50.0 <= x <= 50.0 and -50.0 <= y <= 50.0:
                    # ゼロでない値、または明示的にゼロを設定する場合
                    if abs(x) > 0.1 or abs(y) > 0.1 or (abs(style.shadow.offset_x) < 0.1 and abs(style.shadow.offset_y) < 0.1):
                        # 置き換え
                        struct.pack_into('<f', binary, offset, style.shadow.offset_x)
                        struct.pack_into('<f', binary, offset + 4, style.shadow.offset_y)
                        print(f"  Shadowを適用: X={style.shadow.offset_x:.1f}, Y={style.shadow.offset_y:.1f} @ 0x{offset:04x}")

                        # Blurを探す（X,Yの近くを探索）
                        for delta in [-12, -8, -4, 4, 8, 12]:
                            blur_offset = offset + delta
                            if 0 <= blur_offset + 4 <= len(binary):
                                try:
                                    val = struct.unpack('<f', binary[blur_offset:blur_offset+4])[0]
                                    if 0 <= val <= 100:
                                        struct.pack_into('<f', binary, blur_offset, style.shadow.blur)
                                        print(f"  Shadow Blurを適用: {style.shadow.blur:.1f} @ 0x{blur_offset:04x}")
                                        return binary
                                except:
                                    pass
                        return binary  # Blurが見つからなくてもX,Yは適用済み
            except:
                pass

        print(f"  ⚠️ Shadowの適用位置が見つかりませんでした")
        return binary

    def convert_prsl_to_prtextstyle(self, prsl_filepath: str, output_filepath: str):
        """PRSLファイルを変換"""
        print(f"\n{'='*80}")
        print(f"Converting: {prsl_filepath}")
        print(f"Output: {output_filepath}")
        print('='*80)

        # PRSL解析
        styles = parse_prsl(prsl_filepath)
        if not styles:
            print("ERROR: No styles found in PRSL")
            return False

        print(f"\n✓ Found {len(styles)} styles in PRSL")

        # ベーススタイルのバイナリを取得
        base_binary_data = self._get_style_binary(self.base_style)
        if base_binary_data is None:
            print("ERROR: Could not extract base binary")
            return False

        base_binary, base_binary_elem = base_binary_data
        print(f"✓ Base style binary size: {len(base_binary)} bytes")

        # 最初のスタイルだけを処理（テスト）
        style = styles[0]
        print(f"\n--- Processing Style: {style.name} ---")
        print(f"  Fill: RGB({style.fill.r}, {style.fill.g}, {style.fill.b})")
        if style.shadow.enabled:
            print(f"  Shadow: X={style.shadow.offset_x:.1f}, Y={style.shadow.offset_y:.1f}, Blur={style.shadow.blur:.1f}")

        # バイナリをコピーして変更
        modified_binary = bytearray(base_binary)
        modified_binary = self._apply_fill_color(modified_binary, style)
        modified_binary = self._apply_shadow(modified_binary, style)

        # バイナリを更新
        base_binary_elem.text = base64.b64encode(bytes(modified_binary)).decode('ascii')

        # スタイル名を更新
        name_elem = self.base_style.find('.//Name')
        if name_elem is not None:
            name_elem.text = style.name

        # 保存
        self.tree.write(output_filepath, encoding='utf-8', xml_declaration=True)
        print(f"\n✓ Saved: {output_filepath}")
        return True


def main():
    """テスト実行"""
    if len(sys.argv) < 2:
        print("Usage: python3 prsl_converter_fixed.py <prsl_file> [output_file]")
        print("\nExample:")
        print("  python3 prsl_converter_fixed.py 10styles.prsl output.prtextstyle")
        sys.exit(1)

    prsl_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "converted_fixed.prtextstyle"

    converter = PrtextstyleConverter()
    success = converter.convert_prsl_to_prtextstyle(prsl_file, output_file)

    if success:
        print(f"\n{'='*80}")
        print("✓ Conversion completed successfully!")
        print(f"Please test {output_file} in Premiere Pro")
        print('='*80)
    else:
        print("\n✗ Conversion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
