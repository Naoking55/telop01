#!/usr/bin/env python3
"""
prsl_to_prtextstyle_gui.py のコア機能テスト（GUI以外）
"""

import sys
import os

# GUIモジュールをモックして回避
sys.modules['tkinter'] = type(sys)('tkinter')
sys.modules['tkinter.ttk'] = type(sys)('ttk')
sys.modules['tkinter'].Tk = lambda: None
sys.modules['tkinter'].END = 0

# 必要な部分だけインポート
from prsl_to_prtextstyle_gui import (
    PRSLParser,
    PrtextstyleExporter,
    style_to_params,
    logger
)

def test_conversion():
    """変換機能をテスト"""
    print("="*80)
    print("Testing prsl_to_prtextstyle_gui.py core functionality")
    print("="*80)

    # PRSL解析テスト
    print("\n1. Testing PRSL Parser...")
    prsl_file = "10styles.prsl"

    if not os.path.exists(prsl_file):
        print(f"  ✗ Test file not found: {prsl_file}")
        return

    parser = PRSLParser(prsl_file)
    styles = parser.parse()

    if not styles:
        print(f"  ✗ No styles parsed")
        return

    print(f"  ✓ Parsed {len(styles)} styles")

    # 最初のスタイルを詳細表示
    style = styles[0]
    print(f"\n2. First style details:")
    print(f"  Name: {style.name}")
    print(f"  Font: {style.font_family}, Size: {style.font_size}")
    print(f"  Fill: RGB({style.fill.r}, {style.fill.g}, {style.fill.b})")
    print(f"  Shadow: {'Enabled' if style.shadow.enabled else 'Disabled'}")

    # パラメータ変換テスト
    print(f"\n3. Testing parameter conversion...")
    params = style_to_params(style)
    print(f"  ✓ Converted to PrtextstyleParams")
    print(f"  Fill: ({params.fill_r:.2f}, {params.fill_g:.2f}, {params.fill_b:.2f})")
    print(f"  Shadow enabled: {params.shadow_enabled}")

    # エクスポートテスト
    print(f"\n4. Testing export...")
    output_dir = "test_single_file_output"
    os.makedirs(output_dir, exist_ok=True)

    exporter = PrtextstyleExporter()
    output_path = os.path.join(output_dir, f"{style.name.replace(' ', '_')}.prtextstyle")

    try:
        exporter.export(params, style.name, output_path)

        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"  ✓ Exported successfully: {output_path}")
            print(f"  File size: {size} bytes")
        else:
            print(f"  ✗ Export failed: file not created")

    except Exception as e:
        print(f"  ✗ Export error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("Test completed!")
    print("="*80)

if __name__ == "__main__":
    test_conversion()
