#!/usr/bin/env python3
"""
PRSL→prtextstyle変換テスト
統合コンバーターのテストスクリプト
"""

import logging
import sys
import os

# GUIをインポートしないように、必要な部分だけを読み込む
# prsl_converter_modern.pyからパーサーのみを使用
import xml.etree.ElementTree as ET
import base64
import struct
import math
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field

# データクラス定義（prsl_converter_modern.pyから）
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

# PRSLパーサーのコア機能のみインポート
sys.path.insert(0, os.path.dirname(__file__))

# パーサー関数を直接使用
def decode_base64_floats(b64_text: str) -> List[float]:
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
        return []

def parse_prsl(filepath: str) -> List[Style]:
    """簡易PRSLパーサー（stylelist形式対応）"""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        styles = []

        if root.tag == 'stylelist':
            # stylelist形式
            for styleblock in root.findall('styleblock'):
                style = Style(name=styleblock.attrib.get('name', 'Unnamed'))

                # フォント情報
                text_spec = styleblock.find('text_specification')
                if text_spec is not None:
                    font = text_spec.find('font')
                    if font is not None:
                        family = font.find('family')
                        if family is not None and family.text:
                            style.font_family = family.text.strip()
                        size = font.find('size')
                        if size is not None and size.text:
                            style.font_size = float(size.text)

                # スタイルデータ
                style_data = styleblock.find('style_data')
                if style_data is not None:
                    # Fill
                    face = style_data.find('face')
                    if face is not None:
                        shader = face.find('shader')
                        if shader is not None:
                            colouring = shader.find('colouring')
                            if colouring is not None:
                                # タイプ取得
                                type_elem = colouring.find('type')
                                colour_type = 5  # デフォルト: solid
                                if type_elem is not None and type_elem.text:
                                    colour_type = int(type_elem.text)

                                if colour_type == 5:
                                    # 単色
                                    solid = colouring.find('solid_colour')
                                    if solid is not None:
                                        all_elem = solid.find('all')
                                        if all_elem is not None:
                                            def get_color(name):
                                                c = all_elem.find(name)
                                                if c is not None and c.text:
                                                    return int(float(c.text) * 255)
                                                return 255 if name == 'alpha' else 0

                                            style.fill = Fill(
                                                fill_type="solid",
                                                r=get_color('red'),
                                                g=get_color('green'),
                                                b=get_color('blue'),
                                                a=get_color('alpha')
                                            )

                    # Shadow
                    shadow_elem = style_data.find('shadow')
                    if shadow_elem is not None:
                        on_elem = shadow_elem.find('on')
                        if on_elem is not None and on_elem.text and on_elem.text.strip().lower() == 'true':
                            # Blur
                            softness = shadow_elem.find('softness')
                            blur = 4.0
                            if softness is not None and softness.text:
                                blur = float(softness.text) / 10.0

                            # Offset
                            offset = shadow_elem.find('offset')
                            offset_x, offset_y = 2.0, 2.0
                            if offset is not None:
                                angle_elem = offset.find('angle')
                                mag_elem = offset.find('magnitude')
                                angle = 90.0
                                magnitude = 5.0
                                if angle_elem is not None and angle_elem.text:
                                    angle = float(angle_elem.text)
                                if mag_elem is not None and mag_elem.text:
                                    magnitude = float(mag_elem.text)

                                rad = math.radians(angle)
                                offset_x = magnitude * math.cos(rad)
                                offset_y = -magnitude * math.sin(rad)

                            style.shadow = Shadow(
                                enabled=True,
                                offset_x=offset_x,
                                offset_y=offset_y,
                                blur=blur
                            )

                styles.append(style)

        return styles
    except Exception as e:
        logging.error(f"Parse error: {e}")
        import traceback
        traceback.print_exc()
        return []

from prtextstyle_exporter import (
    PrtextstyleTemplateExporter,
    convert_prsl_style_to_prtextstyle_params
)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_prsl_conversion(prsl_path: str, output_dir: str = "converted_output"):
    """
    PRSLファイルを変換してprtextstyleを生成

    Args:
        prsl_path: PRSLファイルパス
        output_dir: 出力ディレクトリ
    """
    import os

    # 出力ディレクトリ作成
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"=== PRSL Conversion Test: {prsl_path} ===")

    # PRSLをパース
    logger.info("Step 1: Parsing PRSL...")
    styles = parse_prsl(prsl_path)

    if not styles:
        logger.error("No styles found in PRSL file!")
        return

    logger.info(f"Found {len(styles)} styles")

    # 各スタイルの情報を表示
    for i, style in enumerate(styles):
        logger.info(f"\nStyle {i+1}: {style.name}")
        logger.info(f"  Font: {style.font_family}, Size: {style.font_size}")
        logger.info(f"  Fill: {style.fill.fill_type}")

        if style.fill.is_gradient():
            logger.info(f"    Gradient: {len(style.fill.gradient_stops)} stops, angle={style.fill.gradient_angle}°")
        else:
            logger.info(f"    Color: RGB({style.fill.r}, {style.fill.g}, {style.fill.b}), A={style.fill.a}")

        if style.strokes:
            logger.info(f"  Strokes: {len(style.strokes)}")
            for j, stroke in enumerate(style.strokes):
                logger.info(f"    [{j}] Width: {stroke.width}pt, RGB({stroke.r}, {stroke.g}, {stroke.b})")

        if style.shadow.enabled:
            logger.info(f"  Shadow: Enabled")
            logger.info(f"    Offset: ({style.shadow.offset_x}, {style.shadow.offset_y})")
            logger.info(f"    Blur: {style.shadow.blur}")

    # エクスポーターを初期化
    logger.info("\nStep 2: Initializing exporter...")
    exporter = PrtextstyleTemplateExporter()

    # 各スタイルを変換
    logger.info("\nStep 3: Converting styles...")
    for i, style in enumerate(styles):
        try:
            # paramsに変換
            params = convert_prsl_style_to_prtextstyle_params(style)

            # 出力ファイル名
            output_filename = f"{style.name.replace('/', '_').replace(' ', '_')}.prtextstyle"
            output_path = os.path.join(output_dir, output_filename)

            # エクスポート
            logger.info(f"\n  Converting: {style.name}")
            exporter.export(params, style.name, output_path)

            logger.info(f"  ✓ Saved: {output_path}")

        except Exception as e:
            logger.error(f"  ✗ Failed to convert {style.name}: {e}")
            import traceback
            traceback.print_exc()

    logger.info(f"\n=== Conversion Complete ===")
    logger.info(f"Output directory: {output_dir}")


if __name__ == "__main__":
    import sys

    # テスト対象のPRSLファイル
    test_files = [
        "sample_style.prsl",
        "10styles.prsl",
    ]

    for prsl_file in test_files:
        print(f"\n{'='*80}")
        test_prsl_conversion(prsl_file, output_dir=f"converted_{prsl_file.replace('.prsl', '')}")
        print(f"{'='*80}\n")
