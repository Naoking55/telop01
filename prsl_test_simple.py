#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRSL → prtextstyle 変換ツール（1ファイル簡易テスト版）

使い方:
    python prsl_test_simple.py

このスクリプトは:
1. サンプルスタイルを作成
2. プレビュー画像を生成（preview_test.png）
3. prtextstyle ファイルを出力（test_style.prtextstyle）
4. sample_style.prsl がある場合は解析してエクスポート
"""

import os
import sys
import base64
import struct
import math
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

# 画像処理
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import numpy as np
    print("✓ 必要なモジュールが揃っています")
except ImportError as e:
    print(f"❌ エラー: {e}")
    print("\n以下を実行してください:")
    print("  pip install pillow numpy")
    sys.exit(1)

# ==============================================================================
# データクラス
# ==============================================================================

@dataclass
class GradientStop:
    position: float = 0.0
    midpoint: float = 0.5
    r: int = 255
    g: int = 255
    b: int = 255
    a: int = 255

@dataclass
class Fill:
    fill_type: str = "solid"
    r: int = 255
    g: int = 255
    b: int = 255
    a: int = 255
    gradient_stops: List[GradientStop] = field(default_factory=list)
    gradient_angle: float = 0.0

    def is_gradient(self) -> bool:
        return self.fill_type == "gradient"

@dataclass
class Stroke:
    width: float = 1.0
    r: int = 0
    g: int = 0
    b: int = 0
    a: int = 255

@dataclass
class Shadow:
    enabled: bool = False
    offset_x: float = 2.0
    offset_y: float = 2.0
    blur: float = 4.0
    r: int = 0
    g: int = 0
    b: int = 0
    a: int = 120

@dataclass
class Style:
    name: str = "Unnamed Style"
    font_family: str = "Arial"
    font_size: float = 64.0
    fill: Fill = field(default_factory=Fill)
    strokes: List[Stroke] = field(default_factory=list)
    shadow: Shadow = field(default_factory=Shadow)

print("✓ データクラス定義完了")

# ==============================================================================
# PRSLパーサー（簡易版）
# ==============================================================================

def parse_prsl(filepath: str) -> List[Style]:
    """PRSLファイルを解析"""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        styles = []

        for sp in root.findall(".//StyleProjectItem"):
            name_elem = sp.find(".//Name")
            name = name_elem.text.strip() if name_elem is not None and name_elem.text else "Unnamed"

            style = Style(name=name)
            styles.append(style)

        return styles
    except Exception as e:
        print(f"⚠ PRSL解析エラー: {e}")
        return []

print("✓ PRSLパーサー準備完了")

# ==============================================================================
# レンダリング
# ==============================================================================

def render_style(text: str, style: Style, canvas_size=(600, 200)) -> Image.Image:
    """スタイルをレンダリング"""
    W, H = canvas_size

    # ベース画像（ダークグレー背景）
    img = Image.new("RGBA", canvas_size, (40, 40, 40, 255))
    draw = ImageDraw.Draw(img)

    # フォント（デフォルトフォント使用）
    try:
        font = ImageFont.load_default()
    except:
        font = None

    # テキスト位置（中央）
    tx, ty = W // 2, H // 2

    # シャドウ
    if style.shadow.enabled:
        sx = int(tx + style.shadow.offset_x)
        sy = int(ty + style.shadow.offset_y)
        shadow_color = (style.shadow.r, style.shadow.g, style.shadow.b, style.shadow.a)

        # 簡易シャドウ
        for offset in range(3):
            draw.text(
                (sx + offset, sy + offset),
                text,
                font=font,
                fill=shadow_color,
                anchor="mm"
            )

    # ストローク（簡易版）
    for stroke in style.strokes:
        stroke_color = (stroke.r, stroke.g, stroke.b, stroke.a)
        w = int(stroke.width)

        for dx in range(-w, w+1):
            for dy in range(-w, w+1):
                if dx*dx + dy*dy <= w*w:
                    draw.text(
                        (tx + dx, ty + dy),
                        text,
                        font=font,
                        fill=stroke_color,
                        anchor="mm"
                    )

    # 塗り
    fill_color = (style.fill.r, style.fill.g, style.fill.b, style.fill.a)
    draw.text((tx, ty), text, font=font, fill=fill_color, anchor="mm")

    return img

print("✓ レンダリング関数準備完了")

# ==============================================================================
# prtextstyle エクスポート
# ==============================================================================

def build_tlv(tag: int, payload: bytes) -> bytes:
    """TLVバイナリ構築"""
    return struct.pack("<HI", tag, len(payload)) + payload

def export_prtextstyle(style: Style, filepath: str):
    """prtextstyle ファイルとしてエクスポート"""
    blob = b""

    # Font Name
    blob += build_tlv(0x0001, style.font_family.encode("utf-8"))

    # Font Size
    blob += build_tlv(0x0003, struct.pack("<f", float(style.font_size)))

    # Fill (単色のみ)
    blob += build_tlv(0x0004, bytes([style.fill.r, style.fill.g, style.fill.b, style.fill.a]))

    # Strokes
    for stroke in style.strokes:
        s_payload = struct.pack("<fBBBB", float(stroke.width), stroke.r, stroke.g, stroke.b, stroke.a)
        blob += build_tlv(0x0006, s_payload)

    # Shadow
    if style.shadow.enabled:
        s_payload = struct.pack("<fffBBBB",
            float(style.shadow.offset_x),
            float(style.shadow.offset_y),
            float(style.shadow.blur),
            style.shadow.r, style.shadow.g, style.shadow.b, style.shadow.a
        )
        blob += build_tlv(0x0007, s_payload)

    # Base64エンコード
    b64 = base64.b64encode(blob).decode("ascii")

    # XML作成
    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<PremiereData Version="1">
  <Styles>
    <Style>
      <Name>{style.name}</Name>
      <BinaryData Encoding="base64">{b64}</BinaryData>
    </Style>
  </Styles>
</PremiereData>
'''

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(xml_content)

print("✓ エクスポート関数準備完了")

# ==============================================================================
# テスト実行
# ==============================================================================

def main():
    print("\n" + "="*60)
    print("🧪 PRSL変換ツール - 簡易テスト")
    print("="*60 + "\n")

    # テスト1: スタイル作成
    print("📝 テスト1: スタイル作成")
    style = Style(
        name="テストスタイル",
        font_family="Arial",
        font_size=48.0
    )

    # 赤い塗り
    style.fill = Fill(fill_type="solid", r=255, g=80, b=80, a=255)

    # 黒い縁取り
    style.strokes.append(Stroke(width=3.0, r=0, g=0, b=0, a=255))

    # シャドウ
    style.shadow = Shadow(
        enabled=True,
        offset_x=3.0,
        offset_y=3.0,
        blur=2.0,
        r=0, g=0, b=0, a=150
    )

    print(f"  ✓ スタイル作成: {style.name}")
    print(f"    - 塗り: RGB({style.fill.r}, {style.fill.g}, {style.fill.b})")
    print(f"    - ストローク: {len(style.strokes)}個")
    print(f"    - シャドウ: {'有効' if style.shadow.enabled else '無効'}")

    # テスト2: プレビュー生成
    print("\n📝 テスト2: プレビュー画像生成")
    img = render_style("TEST", style, canvas_size=(600, 200))
    preview_file = "preview_test.png"
    img.save(preview_file)
    print(f"  ✓ プレビュー保存: {preview_file}")

    # テスト3: prtextstyle エクスポート
    print("\n📝 テスト3: prtextstyle エクスポート")
    output_file = "test_style.prtextstyle"
    export_prtextstyle(style, output_file)

    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        print(f"  ✓ エクスポート成功: {output_file} ({size} bytes)")
    else:
        print(f"  ✗ エクスポート失敗")

    # テスト4: sample_style.prsl が存在すればテスト
    print("\n📝 テスト4: PRSL解析（オプション）")
    sample_file = "sample_style.prsl"

    if os.path.exists(sample_file):
        print(f"  → {sample_file} を発見")
        styles = parse_prsl(sample_file)
        print(f"  ✓ {len(styles)} 個のスタイルを検出")

        for i, s in enumerate(styles, 1):
            output = f"exported_{i}_{s.name}.prtextstyle"
            export_prtextstyle(s, output)
            print(f"    {i}. {s.name} → {output}")
    else:
        print(f"  ⚠ {sample_file} が見つかりません（スキップ）")

    # サマリー
    print("\n" + "="*60)
    print("✅ テスト完了！")
    print("="*60)
    print("\n生成されたファイル:")

    files = [preview_file, output_file]
    if os.path.exists(sample_file):
        files.extend([f for f in os.listdir('.') if f.startswith('exported_') and f.endswith('.prtextstyle')])

    for f in files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"  📄 {f} ({size} bytes)")

    print("\n次のステップ:")
    print("  1. preview_test.png を開いてプレビューを確認")
    print("  2. test_style.prtextstyle を Adobe Premiere で読み込み")
    print("  3. 問題なければ prsl_converter_modern.py でGUI版を使用")
    print()

if __name__ == "__main__":
    main()
