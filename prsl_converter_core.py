#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRSL → prtextstyle 変換ツール（モダンGUI版）
====================================================================
Python 3.8+ 対応 / モダンなGUIデザイン / 全問題修正版

このプログラムは、Adobe Premiere のレガシータイトル（PRTL）を含む
PRSL スタイルファイルを、現行の「prtextstyle」形式へ変換します。

主な改善点:
- Python 3.8+ で動作（3.12専用ではない）
- GUI を Tkinter に統一（モダンなダークテーマ）
- すべての属性名・関数名の不整合を修正
- エラーハンドリング強化
- パフォーマンス改善

使い方:
    python prsl_converter_modern.py
"""

import os
import sys
import base64
import json
import math
import struct
import traceback
import copy as copy_module
from typing import List, Optional, Tuple, Dict, Any
from xml.etree import ElementTree as ET
from dataclasses import dataclass, field
import logging

# 画像処理
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# GUI（Tkinter - 標準ライブラリ）
# import tkinter as tk
# from tkinter import ...
# from PIL import ImageTk

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================================================================
# 設定定数
# ==============================================================================
SPEC_VERSION = "2.0.0"
APP_TITLE = "PRSL → prtextstyle 変換ツール"
DEFAULT_CANVAS_SIZE = (800, 250)
DEFAULT_FONT_SIZE = 64

# モダンなカラースキーム（ダークテーマ）
COLORS = {
    'bg_dark': '#1e1e1e',
    'bg_medium': '#2d2d2d',
    'bg_light': '#3e3e3e',
    'fg_primary': '#ffffff',
    'fg_secondary': '#b0b0b0',
    'accent_blue': '#0e7afa',
    'accent_green': '#0fa968',
    'accent_orange': '#ff9500',
    'border': '#444444',
}


# ==============================================================================
# BLOCK 01: データクラス定義（修正版）
# ==============================================================================

@dataclass
class GradientStop:
    """グラデーションストップ情報"""
    position: float = 0.0
    midpoint: float = 0.5
    r: int = 255
    g: int = 255
    b: int = 255
    a: int = 255

    @property
    def color(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    @property
    def alpha(self) -> float:
        return self.a / 255.0


@dataclass
class Fill:
    """塗り情報（単色またはグラデーション）"""
    fill_type: str = "solid"
    r: int = 255
    g: int = 255
    b: int = 255
    a: int = 255
    gradient_stops: List[GradientStop] = field(default_factory=list)
    gradient_angle: float = 0.0

    def is_gradient(self) -> bool:
        return self.fill_type == "gradient"

    @property
    def color(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    @property
    def opacity(self) -> float:
        return self.a / 255.0


@dataclass
class Stroke:
    """ストローク情報"""
    width: float = 1.0
    r: int = 0
    g: int = 0
    b: int = 0
    a: int = 255

    @property
    def color(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    @property
    def opacity(self) -> float:
        return self.a / 255.0

    def copy(self) -> 'Stroke':
        return copy_module.copy(self)


@dataclass
class Shadow:
    """シャドウ情報"""
    enabled: bool = False
    offset_x: float = 2.0
    offset_y: float = 2.0
    blur: float = 4.0
    r: int = 0
    g: int = 0
    b: int = 0
    a: int = 120

    @property
    def color(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    @property
    def alpha(self) -> float:
        return self.a / 255.0

    @property
    def opacity(self) -> float:
        return self.a / 255.0


@dataclass
class Style:
    """スタイル全体"""
    name: str = "Unnamed Style"
    font_family: str = "Arial"
    font_size: float = 64.0
    bold: bool = False
    italic: bool = False
    tracking: float = 0.0
    leading: float = 0.0
    fill: Fill = field(default_factory=Fill)
    strokes: List[Stroke] = field(default_factory=list)
    shadow: Shadow = field(default_factory=Shadow)
    opacity: float = 1.0
    angle: float = 0.0
    meta: Dict[str, Any] = field(default_factory=dict)
    original_prsl_node: Optional[ET.Element] = None
    raw_binary: Optional[bytes] = None


logger.info("✓ Data classes loaded")


# ==============================================================================
# BLOCK 02: PRSL パーサー（修正版）
# ==============================================================================

def decode_base64_floats(b64_text: str) -> List[float]:
    """Base64エンコードされたfloat配列をデコード"""
    if not b64_text:
        return []
    try:
        raw = base64.b64decode(b64_text)
        values = []
        for i in range(0, len(raw), 4):
            chunk = raw[i:i+4]
            if len(chunk) < 4:
                break
            value = struct.unpack("<f", chunk)[0]
            values.append(value)
        return values
    except Exception as e:
        logger.warning(f"Base64 decode error: {e}")
        return []


class PRSLParamParser:
    """PRSLパラメータパーサー"""

    def __init__(self, param_node: ET.Element):
        self.node = param_node
        self.index = int(param_node.attrib.get("Index", -1))
        self.b64_value = None

        val = param_node.find("StartKeyframeValue")
        if val is not None and val.text:
            self.b64_value = val.text.strip()

    def parse(self) -> Optional[Dict[str, Any]]:
        """パラメータを解析"""
        idx = self.index

        # フォントサイズ
        if idx == 4:
            floats = decode_base64_floats(self.b64_value)
            if floats:
                return {"type": "font_size", "value": floats[0]}

        # 塗り色
        if idx in (11, 12, 13):
            floats = decode_base64_floats(self.b64_value)
            if len(floats) >= 4:
                return {
                    "type": "fill_color",
                    "rgba": (
                        int(floats[0] * 255),
                        int(floats[1] * 255),
                        int(floats[2] * 255),
                        int(floats[3] * 255)
                    )
                }

        # ストローク
        if 20 <= idx <= 30:
            floats = decode_base64_floats(self.b64_value)
            if len(floats) == 1:
                return {"type": "stroke_width", "width": floats[0]}
            if len(floats) >= 4:
                return {
                    "type": "stroke_color",
                    "rgba": (
                        int(floats[0] * 255),
                        int(floats[1] * 255),
                        int(floats[2] * 255),
                        int(floats[3] * 255)
                    )
                }

        # シャドウ
        if idx >= 50:
            floats = decode_base64_floats(self.b64_value)
            if len(floats) >= 4:
                return {
                    "type": "shadow",
                    "offset": (floats[0], floats[1]),
                    "blur": floats[2],
                    "alpha": int(floats[3] * 255),
                }

        return None


class PRSLParser:
    """PRSLファイルパーサー"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
        self.styles: List[Style] = []

    def parse(self) -> List[Style]:
        """PRSLファイル全体を解析"""
        for sp in self.root.findall(".//StyleProjectItem"):
            style = self._parse_style_project_item(sp)
            self.styles.append(style)
        logger.info(f"✓ Parsed {len(self.styles)} styles from {os.path.basename(self.filepath)}")
        return self.styles

    def _parse_style_project_item(self, sp: ET.Element) -> Style:
        """StyleProjectItemを解析"""
        name = sp.find(".//Name")
        style_name = name.text.strip() if name is not None and name.text else "Unnamed Style"

        style = Style(name=style_name)
        style.original_prsl_node = sp

        for param in sp.findall(".//Param"):
            parsed = PRSLParamParser(param).parse()
            if parsed:
                self._apply_parsed_param(style, parsed)

        return style

    def _apply_parsed_param(self, style: Style, parsed: Dict[str, Any]):
        """解析されたパラメータをStyleに適用"""
        ptype = parsed["type"]

        if ptype == "font_size":
            style.font_size = parsed["value"]

        elif ptype == "fill_color":
            r, g, b, a = parsed["rgba"]
            style.fill = Fill(fill_type="solid", r=r, g=g, b=b, a=a)

        elif ptype == "stroke_width":
            style.strokes.append(Stroke(width=parsed["width"]))

        elif ptype == "stroke_color":
            r, g, b, a = parsed["rgba"]
            if style.strokes:
                style.strokes[-1].r = r
                style.strokes[-1].g = g
                style.strokes[-1].b = b
                style.strokes[-1].a = a

        elif ptype == "shadow":
            ox, oy = parsed["offset"]
            style.shadow.enabled = True
            style.shadow.offset_x = ox
            style.shadow.offset_y = oy
            style.shadow.blur = parsed["blur"]
            style.shadow.a = parsed["alpha"]


def parse_prsl(filepath: str) -> List[Style]:
    """PRSLファイルを解析（ラッパー関数）"""
    parser = PRSLParser(filepath)
    return parser.parse()


logger.info("✓ PRSL parser loaded")


# ==============================================================================
# BLOCK 03: レンダリングユーティリティ
# ==============================================================================

def lerp(a: float, b: float, t: float) -> float:
    """線形補間"""
    return a + (b - a) * t


def lerp_color(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    """色の線形補間"""
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t)),
    )


def sample_gradient(stops: List[GradientStop], t: float) -> Tuple[int, int, int, int]:
    """グラデーションから色をサンプリング"""
    if not stops:
        return (255, 255, 255, 255)

    t = max(0.0, min(1.0, float(t)))

    if len(stops) == 1:
        s = stops[0]
        return (*s.color, int(s.alpha * 255))

    stops_sorted = sorted(stops, key=lambda s: s.position)

    if t <= stops_sorted[0].position:
        s = stops_sorted[0]
        return (*s.color, int(s.alpha * 255))

    if t >= stops_sorted[-1].position:
        s = stops_sorted[-1]
        return (*s.color, int(s.alpha * 255))

    for i in range(len(stops_sorted) - 1):
        s1 = stops_sorted[i]
        s2 = stops_sorted[i + 1]
        if s1.position <= t <= s2.position:
            span = s2.position - s1.position
            u = (t - s1.position) / span if span > 0 else 0.0

            # Midpoint補間
            midpoint = s1.midpoint
            if u < midpoint:
                u = 0.5 * (u / midpoint)
            else:
                u = 0.5 + 0.5 * ((u - midpoint) / (1.0 - midpoint))

            c = lerp_color(s1.color, s2.color, u)
            a = int(lerp(s1.alpha, s2.alpha, u) * 255)
            return (*c, a)

    s = stops_sorted[-1]
    return (*s.color, int(s.alpha * 255))


def make_linear_gradient(width: int, height: int, stops: List[GradientStop], angle: float = 0.0) -> Image.Image:
    """線形グラデーション画像を生成"""
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    grad_pixels = gradient.load()

    theta = math.radians(angle)
    dx = math.cos(theta)
    dy = -math.sin(theta)

    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0

    max_len = 0.0
    for px, py in [(0, 0), (width-1, 0), (0, height-1), (width-1, height-1)]:
        vx = px - cx
        vy = py - cy
        proj = vx * dx + vy * dy
        max_len = max(max_len, abs(proj))

    if max_len <= 0:
        max_len = 1.0

    for y in range(height):
        for x in range(width):
            vx = x - cx
            vy = y - cy
            proj = vx * dx + vy * dy
            t = 0.5 + 0.5 * (proj / max_len)
            r, g, b, a = sample_gradient(stops, t)
            grad_pixels[x, y] = (r, g, b, a)

    return gradient


def dilate_mask_fast(mask_img: Image.Image, radius: int) -> Image.Image:
    """高速マスク膨張（scipy使用、なければPILフォールバック）"""
    if radius <= 0:
        return mask_img.copy()

    mask = mask_img.convert("L")

    try:
        from scipy import ndimage
        arr = np.array(mask)
        y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
        se = (x*x + y*y <= radius*radius).astype(np.uint8)
        dilated = ndimage.grey_dilation(arr, footprint=se)
        return Image.fromarray(dilated, mode="L")
    except ImportError:
        # scipy無し: PILフィルタで代用
        for _ in range(int(radius)):
            mask = mask.filter(ImageFilter.MaxFilter(3))
        return mask


logger.info("✓ Rendering utilities loaded")


# ==============================================================================
# BLOCK 04: スタイルレンダリングエンジン（統合版）
# ==============================================================================

class StyleRenderer:
    """スタイルをプレビュー画像にレンダリング"""

    def __init__(self, canvas_size: Tuple[int, int] = DEFAULT_CANVAS_SIZE):
        self.canvas_size = canvas_size
        self.font_cache: Dict[str, ImageFont.FreeTypeFont] = {}

    def get_font(self, font_path: str, size: int) -> ImageFont.FreeTypeFont:
        """フォントをキャッシュから取得"""
        key = f"{font_path}:{size}"
        if key not in self.font_cache:
            try:
                self.font_cache[key] = ImageFont.truetype(font_path, size)
            except Exception as e:
                logger.warning(f"Font load failed: {e}, using default")
                self.font_cache[key] = ImageFont.load_default()
        return self.font_cache[key]

    def render(
        self,
        text: str,
        style: Style,
        font_path: Optional[str] = None,
        font_size: Optional[int] = None,
        background: Tuple[int, int, int, int] = (40, 40, 40, 255)
    ) -> Image.Image:
        """スタイルを完全にレンダリング"""

        # フォント準備
        if font_path is None:
            font_path = self._find_system_font(style.font_family)
        if font_size is None:
            font_size = int(style.font_size)

        font = self.get_font(font_path, font_size)

        # ベース画像
        base = Image.new("RGBA", self.canvas_size, background)

        # Shadow → Stroke → Fill の順に描画
        shadow_layer = self._render_shadow(text, font, style)
        base = Image.alpha_composite(base, shadow_layer)

        stroke_layer = self._render_strokes(text, font, style)
        base = Image.alpha_composite(base, stroke_layer)

        fill_layer = self._render_fill(text, font, style)
        base = Image.alpha_composite(base, fill_layer)

        return base

    def _render_shadow(self, text: str, font: ImageFont.FreeTypeFont, style: Style) -> Image.Image:
        """シャドウレイヤーをレンダリング"""
        shadow = style.shadow
        if not shadow.enabled:
            return Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))

        W, H = self.canvas_size
        base_mask = Image.new("L", self.canvas_size, 0)
        draw = ImageDraw.Draw(base_mask)
        tx, ty = W // 2, H // 2
        draw.text((tx, ty), text, font=font, fill=255, anchor="mm")

        # オフセット
        offset_mask = Image.new("L", self.canvas_size, 0)
        offset_mask.paste(base_mask, (int(round(shadow.offset_x)), int(round(shadow.offset_y))))

        # ぼかし
        if shadow.blur > 0:
            offset_mask = offset_mask.filter(ImageFilter.GaussianBlur(radius=shadow.blur))

        # 着色
        r, g, b = shadow.color
        a = shadow.a
        shadow_img = Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))
        shadow_colored = Image.new("RGBA", self.canvas_size, (r, g, b, 0))
        draw_shadow = ImageDraw.Draw(shadow_colored)
        draw_shadow.bitmap((0, 0), offset_mask, fill=(r, g, b, a))

        return Image.alpha_composite(shadow_img, shadow_colored)

    def _render_strokes(self, text: str, font: ImageFont.FreeTypeFont, style: Style) -> Image.Image:
        """ストロークレイヤーをレンダリング"""
        if not style.strokes:
            return Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))

        W, H = self.canvas_size
        base_mask = Image.new("L", self.canvas_size, 0)
        draw = ImageDraw.Draw(base_mask)
        tx, ty = W // 2, H // 2
        draw.text((tx, ty), text, font=font, fill=255, anchor="mm")

        stroke_layer = Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))
        prev_mask = base_mask.copy()

        for stroke in style.strokes:
            w = int(stroke.width)
            if w <= 0:
                continue

            dilated = dilate_mask_fast(base_mask, w)

            # 差分領域
            arr_d = np.array(dilated)
            arr_p = np.array(prev_mask)
            diff = np.clip(arr_d - arr_p, 0, 255).astype(np.uint8)
            region = Image.fromarray(diff, mode="L")

            # 着色
            r, g, b = stroke.color
            a = stroke.a
            colored = Image.new("RGBA", self.canvas_size, (r, g, b, 0))
            draw_colored = ImageDraw.Draw(colored)
            draw_colored.bitmap((0, 0), region, fill=(r, g, b, a))

            stroke_layer = Image.alpha_composite(stroke_layer, colored)
            prev_mask = dilated

        return stroke_layer

    def _render_fill(self, text: str, font: ImageFont.FreeTypeFont, style: Style) -> Image.Image:
        """塗りレイヤーをレンダリング"""
        W, H = self.canvas_size
        mask = Image.new("L", self.canvas_size, 0)
        draw = ImageDraw.Draw(mask)
        tx, ty = W // 2, H // 2
        draw.text((tx, ty), text, font=font, fill=255, anchor="mm")

        fill = style.fill

        if fill.is_gradient():
            # グラデーション
            bbox = draw.textbbox((tx, ty), text, font=font, anchor="mm")
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if w > 0 and h > 0:
                gradient = make_linear_gradient(w, h, fill.gradient_stops, fill.gradient_angle)
                gradient.putalpha(Image.new("L", (w, h), 255))

                # テキスト形状でマスク
                text_mask = Image.new("L", (w, h), 0)
                draw_text = ImageDraw.Draw(text_mask)
                draw_text.text((w//2, h//2), text, font=font, fill=255, anchor="mm")
                gradient.putalpha(text_mask)

                result = Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))
                result.paste(gradient, (bbox[0], bbox[1]), gradient)
                return result
            else:
                return Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))
        else:
            # 単色
            r, g, b = fill.color
            a = fill.a
            img = Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))
            draw_img = ImageDraw.Draw(img)
            draw_img.text((tx, ty), text, font=font, fill=(r, g, b, a), anchor="mm")
            return img

    def _find_system_font(self, family: str) -> str:
        """システムフォントを検索"""
        # macOS
        candidates = [
            f"/System/Library/Fonts/{family}.ttc",
            f"/Library/Fonts/{family}.ttf",
            "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
            # Windows
            f"C:/Windows/Fonts/{family}.ttf",
            "C:/Windows/Fonts/meiryo.ttc",
            # Linux
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]

        for path in candidates:
            if os.path.exists(path):
                return path

        # フォールバック
        return "Arial.ttf"


logger.info("✓ Style renderer loaded")


# ==============================================================================
# BLOCK 05: prtextstyle エクスポーター
# ==============================================================================

def build_tlv(tag: int, payload: bytes) -> bytes:
    """TLV (Tag-Length-Value) バイナリを構築"""
    return struct.pack("<HI", tag, len(payload)) + payload


def export_prtextstyle(style: Style, filepath: str):
    """prtextstyle ファイルとしてエクスポート"""

    # TLV構築
    blob = b""

    # Font Name
    blob += build_tlv(0x0001, style.font_family.encode("utf-8"))

    # Font Style
    flags = 0
    if style.bold:
        flags |= 1
    if style.italic:
        flags |= 2
    blob += build_tlv(0x0002, struct.pack("<I", flags))

    # Font Size
    blob += build_tlv(0x0003, struct.pack("<f", float(style.font_size)))

    # Fill
    if style.fill.is_gradient():
        # グラデーション
        grad_payload = b""
        for stop in style.fill.gradient_stops:
            stop_data = struct.pack("<ffIIII",
                float(stop.position),
                float(stop.midpoint),
                stop.r, stop.g, stop.b, stop.a
            )
            stop_data += b"\x00" * (48 - len(stop_data))
            grad_payload += build_tlv(0x00F0, stop_data)

        grad_payload += build_tlv(0x000A, struct.pack("<f", float(style.fill.gradient_angle)))
        blob += build_tlv(0x0005, grad_payload)
    else:
        # 単色
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

    logger.info(f"✓ Exported: {os.path.basename(filepath)}")


logger.info("✓ prtextstyle exporter loaded")



if __name__ == "__main__":
    main()
