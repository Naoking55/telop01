#!/usr/bin/env python3
"""
CLI方式でのテスト（GUI v2.1が使うべきロジック）
"""

import sys
import re
import base64

sys.path.insert(0, '/home/user/telop01')
from FINAL_prsl_converter import (
    get_color_structure,
    replace_color_bytes,
    convert_prsl_to_prtextstyle_v2,
    MARKER
)

print("="*60)
print("CLI方式テスト（GUI v2.1の期待動作）")
print("="*60)

prsl_file = "/tmp/10styles.prsl"
template_file = "/tmp/10styles.prtextstyle"
output_file = "/home/user/telop01/test_cli_output.prtextstyle"

print(f"\n入力:")
print(f"  PRSL: {prsl_file}")
print(f"  Template: {template_file}")
print(f"  Output: {output_file}")

print(f"\n実行中...")
try:
    convert_prsl_to_prtextstyle_v2(prsl_file, template_file, output_file)

    # 出力ファイルのサイズ確認
    import os
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        print(f"\n✓ 出力ファイル生成成功")
        print(f"  サイズ: {size} bytes ({size/1024:.1f} KB)")

        if size < 10000:
            print(f"  ⚠️ サイズが小さすぎます！（期待: 100KB以上）")
        else:
            print(f"  ✓ サイズ正常")

except Exception as e:
    print(f"\n✗ エラー: {e}")
    import traceback
    traceback.print_exc()
