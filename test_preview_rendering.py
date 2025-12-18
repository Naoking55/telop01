#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プレビューレンダリングのテスト
"""

import sys
import os
sys.path.insert(0, '/home/user/telop01')

print("=" * 70)
print("プレビューレンダリングテスト")
print("=" * 70)

# PRSLファイルを読み込み
from prsl_parser_stylelist import parse_prsl_stylelist

test_file = "10styles.prsl"
styles = parse_prsl_stylelist(test_file)
print(f"\n✓ {len(styles)} スタイルを読み込み")

if not styles:
    print("✗ スタイルが見つかりません")
    sys.exit(1)

# 最初のスタイルを使用
style = styles[0]
print(f"\nスタイル: {style.name}")
print(f"  フォント: {style.font_family} ({style.font_size}pt)")
print(f"  塗り: {style.fill.fill_type}")
print(f"  塗り色: RGB({style.fill.r}, {style.fill.g}, {style.fill.b}, {style.fill.a})")
print(f"  color プロパティ: {style.fill.color}")  # これがあるか確認
print(f"  シャドウ: {style.shadow.enabled}")
if style.shadow.enabled:
    print(f"    オフセット: ({style.shadow.offset_x}, {style.shadow.offset_y})")
    print(f"    ぼかし: {style.shadow.blur}")
    print(f"    色: RGB({style.shadow.r}, {style.shadow.g}, {style.shadow.b}, {style.shadow.a})")
    print(f"    color プロパティ: {style.shadow.color}")  # これがあるか確認

# レンダリングテスト
print("\n" + "=" * 70)
print("レンダリング開始")
print("=" * 70)

try:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np

    print("✓ PIL/Pillow インポート成功")
    print("✓ NumPy インポート成功")

    # 簡単なテスト画像を作成
    print("\n[1] 基本的な画像作成テスト...")
    test_img = Image.new("RGBA", (800, 250), (40, 40, 40, 255))
    print(f"  ✓ 画像作成成功: {test_img.size}, {test_img.mode}")

    # フォント取得テスト
    print("\n[2] フォント取得テスト...")
    try:
        # デフォルトフォントを試す
        font = ImageFont.load_default()
        print(f"  ✓ デフォルトフォント取得成功")
    except Exception as e:
        print(f"  ✗ フォント取得失敗: {e}")
        font = None

    # テキスト描画テスト
    if font:
        print("\n[3] テキスト描画テスト...")
        draw = ImageDraw.Draw(test_img)
        draw.text((400, 125), "テスト", font=font, fill=(255, 0, 0, 255), anchor="mm")
        print(f"  ✓ テキスト描画成功")

        # 保存
        output_file = "test_preview_simple.png"
        test_img.save(output_file)
        print(f"  ✓ 保存成功: {output_file}")
        print(f"    サイズ: {os.path.getsize(output_file)} bytes")

    # StyleRendererを使ったテスト
    print("\n" + "=" * 70)
    print("StyleRenderer テスト")
    print("=" * 70)

    # StyleRendererを直接インポートせずに、関数だけをテスト
    # （tkinter エラーを避けるため）

    print("\n[4] 単色塗りのテスト画像を作成...")
    img = Image.new("RGBA", (800, 250), (40, 40, 40, 255))
    draw = ImageDraw.Draw(img)

    # スタイルの色を使用
    r, g, b, a = style.fill.r, style.fill.g, style.fill.b, style.fill.a
    print(f"  使用する色: RGBA({r}, {g}, {b}, {a})")

    draw.text((400, 125), "テスト", font=font, fill=(r, g, b, a), anchor="mm")

    output_file = "test_preview_styled.png"
    img.save(output_file)
    print(f"  ✓ 保存成功: {output_file}")
    print(f"    サイズ: {os.path.getsize(output_file)} bytes")

    print("\n" + "=" * 70)
    print("✅ レンダリングテスト完了")
    print("=" * 70)
    print("\n生成されたファイル:")
    print("  - test_preview_simple.png")
    print("  - test_preview_styled.png")

except ImportError as e:
    print(f"✗ インポートエラー: {e}")
    import traceback
    traceback.print_exc()

except Exception as e:
    print(f"✗ エラー: {e}")
    import traceback
    traceback.print_exc()
