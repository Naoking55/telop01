#!/usr/bin/env python3
"""
PRSL → prtextstyle 変換ツール（RGB Bytes対応版）
Fill色をRGB Bytes形式で変更
"""

import os
import sys
import struct
import xml.etree.ElementTree as ET
import base64
from typing import List

# 既存のPRSLパーサーを再利用
from test_prsl_conversion import parse_prsl, Style


class PrtextstyleConverterV2:
    """RGB Bytes形式対応のコンバーター"""

    def __init__(self, base_filepath: str = "TEMPLATE_SolidFill_White.prtextstyle"):
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

    def _apply_fill_color_rgb_bytes(self, binary: bytearray, style: Style) -> bytearray:
        """Fill色をRGB Bytes形式で適用"""
        if style.fill.is_gradient():
            return binary  # グラデーションは未対応

        target_r = style.fill.r
        target_g = style.fill.g
        target_b = style.fill.b

        # RGB Bytes (255,255,255) を探して置き換え
        replaced_count = 0
        for offset in range(0, len(binary) - 2):
            r = binary[offset]
            g = binary[offset+1]
            b = binary[offset+2]

            # 白 (255,255,255) を探す
            if r == 255 and g == 255 and b == 255:
                # 置き換え
                binary[offset] = target_r
                binary[offset+1] = target_g
                binary[offset+2] = target_b
                replaced_count += 1
                print(f"  Fill色を適用 (RGB Bytes): RGB({target_r}, {target_g}, {target_b}) @ 0x{offset:04x}")

        if replaced_count == 0:
            print(f"  ⚠️ Fill色の適用位置が見つかりませんでした")
        else:
            print(f"  ✓ Fill色を{replaced_count}箇所に適用しました")

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

        # 最初のスタイルだけを処理
        style = styles[0]
        print(f"\n--- Processing Style: {style.name} ---")
        print(f"  Fill: RGB({style.fill.r}, {style.fill.g}, {style.fill.b})")

        # バイナリをコピーして変更
        modified_binary = bytearray(base_binary)
        modified_binary = self._apply_fill_color_rgb_bytes(modified_binary, style)

        # バイナリを更新
        base_binary_elem.text = base64.b64encode(bytes(modified_binary)).decode('ascii')

        # スタイル名を更新
        name_elem = self.base_style.find('.//Name')
        if name_elem is not None:
            name_elem.text = f"【RGB Bytes版】{style.name} - RGB({style.fill.r},{style.fill.g},{style.fill.b})"

        # 保存
        self.tree.write(output_filepath, encoding='utf-8', xml_declaration=True)
        print(f"\n✓ Saved: {output_filepath}")
        print(f"  → Premiereでテストしてください")
        return True


def main():
    """テスト実行"""
    if len(sys.argv) < 2:
        print("Usage: python3 prsl_converter_v2.py <prsl_file> [output_file]")
        print("\nExample:")
        print("  python3 prsl_converter_v2.py 10styles.prsl output.prtextstyle")
        sys.exit(1)

    prsl_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "converted_rgb_bytes.prtextstyle"

    converter = PrtextstyleConverterV2()
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
