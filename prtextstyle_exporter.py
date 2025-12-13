#!/usr/bin/env python3
"""
prtextstyle Exporter - FlatBuffers形式対応版
==================================================
解析結果を基に、PRSL Styleからprtextstyleバイナリを生成

アプローチ:
1. テンプレートベース: シンプルなprtextstyleを基に変更
2. 既知のパラメータ位置を使用（解析結果から）
3. Shadow/Gradient/Strokeを適切に追加・変更
"""

import struct
import base64
import xml.etree.ElementTree as ET
from typing import Optional, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class GradientStop:
    """グラデーションストップ"""
    position: float
    r: float  # 0.0-1.0
    g: float
    b: float
    a: float


@dataclass
class PrtextstyleParams:
    """prtextstyle パラメータ"""
    # Font
    font_family: str = "Arial"
    font_size: float = 64.0

    # Fill
    fill_type: str = "solid"  # "solid" or "gradient"
    fill_r: float = 1.0
    fill_g: float = 1.0
    fill_b: float = 1.0
    fill_a: float = 1.0
    gradient_stops: List[GradientStop] = None
    gradient_angle: float = 0.0

    # Stroke
    stroke_enabled: bool = False
    stroke_width: float = 0.0
    stroke_r: float = 0.0
    stroke_g: float = 0.0
    stroke_b: float = 0.0
    stroke_a: float = 1.0

    # Shadow
    shadow_enabled: bool = False
    shadow_x: float = 0.0
    shadow_y: float = 0.0
    shadow_blur: float = 0.0
    shadow_r: float = 0.0
    shadow_g: float = 0.0
    shadow_b: float = 0.0
    shadow_a: float = 0.5


class PrtextstyleTemplateExporter:
    """テンプレートベースのprtextstyleエクスポーター"""

    def __init__(self, template_path: str = "prtextstyle/100 New Fonstyle.prtextstyle"):
        """
        Args:
            template_path: ベースとなるprtextstyleファイル
        """
        self.template_path = template_path
        self.template_binary = None
        self.template_style_name = None

        # テンプレート読み込み
        self._load_template()

    def _load_template(self):
        """テンプレートファイルを読み込み"""
        try:
            tree = ET.parse(self.template_path)
            root = tree.getroot()

            # 最初のStyleProjectItemを使用
            for style_item in root.findall('.//StyleProjectItem'):
                name_elem = style_item.find('.//Name')
                if name_elem is not None:
                    self.template_style_name = name_elem.text

                    # バイナリ取得
                    component_ref_elem = style_item.find('.//Component[@ObjectRef]')
                    component_ref = component_ref_elem.get('ObjectRef')
                    vfc = root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")
                    first_param_ref = vfc.find(".//Param[@Index='0']")
                    param_obj_ref = first_param_ref.get('ObjectRef')
                    arb_param = root.find(f".//ArbVideoComponentParam[@ObjectID='{param_obj_ref}']")
                    binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")

                    self.template_binary = base64.b64decode(binary_elem.text.strip())
                    logger.info(f"Template loaded: {self.template_style_name} ({len(self.template_binary)} bytes)")
                    break

        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            # フォールバック: 最小限のバイナリ（732バイト）
            self.template_binary = b'\x00' * 732
            self.template_style_name = "Template"

    def export(self, params: PrtextstyleParams, style_name: str, output_path: str):
        """
        パラメータからprtextstyleファイルを生成

        Args:
            params: スタイルパラメータ
            style_name: スタイル名
            output_path: 出力ファイルパス
        """
        # テンプレートをコピー
        binary = bytearray(self.template_binary)

        # パラメータを適用
        binary = self._apply_fill(binary, params)
        binary = self._apply_stroke(binary, params)
        binary = self._apply_shadow(binary, params)
        binary = self._apply_gradient(binary, params)

        # XMLに埋め込んで保存
        self._save_as_prtextstyle(bytes(binary), style_name, output_path)

        logger.info(f"Exported: {output_path} ({len(binary)} bytes)")

    def _apply_fill(self, binary: bytearray, params: PrtextstyleParams) -> bytearray:
        """Fill色を適用（単色のみ、グラデーションは別処理）"""
        if params.fill_type != "solid":
            return binary

        # Fill色の位置を探す
        # 解析結果: 0x0100付近にRGBA float (16 bytes)
        fill_offset = self._find_fill_color_offset(binary)

        if fill_offset is not None:
            struct.pack_into('<f', binary, fill_offset, params.fill_r)
            struct.pack_into('<f', binary, fill_offset + 4, params.fill_g)
            struct.pack_into('<f', binary, fill_offset + 8, params.fill_b)
            struct.pack_into('<f', binary, fill_offset + 12, params.fill_a)
            logger.debug(f"Fill color applied at 0x{fill_offset:04x}")

        return binary

    def _apply_stroke(self, binary: bytearray, params: PrtextstyleParams) -> bytearray:
        """ストロークを適用"""
        if not params.stroke_enabled:
            return binary

        # ストローク幅の位置を探す（解析結果: 0x0180付近）
        stroke_offset = self._find_stroke_width_offset(binary)

        if stroke_offset is not None:
            struct.pack_into('<f', binary, stroke_offset, params.stroke_width)
            logger.debug(f"Stroke width applied at 0x{stroke_offset:04x}: {params.stroke_width}")

            # ストローク色（ストローク幅の近く）
            # TODO: 正確な位置を特定

        return binary

    def _apply_shadow(self, binary: bytearray, params: PrtextstyleParams) -> bytearray:
        """シャドウを適用"""
        if not params.shadow_enabled:
            return binary

        # シャドウブロックの有無を確認
        if len(binary) <= 732:
            # シャドウなし → シャドウブロックを追加する必要がある
            # TODO: シャドウブロック追加の実装（Phase 2）
            logger.warning("Shadow block addition not yet implemented")
            return binary

        # 既存のシャドウブロック内のパラメータを変更
        shadow_xy_pairs = self._find_shadow_xy_offsets(binary)

        if shadow_xy_pairs:
            # 最初のシャドウのX,Yを変更
            offset = shadow_xy_pairs[0]['offset']
            struct.pack_into('<f', binary, offset, params.shadow_x)
            struct.pack_into('<f', binary, offset + 4, params.shadow_y)
            logger.debug(f"Shadow X,Y applied at 0x{offset:04x}: ({params.shadow_x}, {params.shadow_y})")

            # Blurを変更（X,Yの±4-12バイト付近を探索）
            for delta in [-12, -8, -4, 4, 8, 12]:
                blur_offset = offset + delta
                if 0 <= blur_offset + 4 <= len(binary):
                    try:
                        val = struct.unpack('<f', binary[blur_offset:blur_offset+4])[0]
                        if 0 <= val <= 100:  # 妥当なBlur値
                            struct.pack_into('<f', binary, blur_offset, params.shadow_blur)
                            logger.debug(f"Shadow blur applied at 0x{blur_offset:04x}: {params.shadow_blur}")
                            break
                    except:
                        pass

        return binary

    def _apply_gradient(self, binary: bytearray, params: PrtextstyleParams) -> bytearray:
        """グラデーションを適用"""
        if params.fill_type != "gradient" or not params.gradient_stops:
            return binary

        # グラデーションストップの位置を探す
        # 解析結果: [Position 4B][Alpha 4B] の8バイトペア
        gradient_offsets = self._find_gradient_stop_offsets(binary)

        # ストップ数が一致する場合のみ適用
        if len(gradient_offsets) == len(params.gradient_stops):
            for i, stop in enumerate(params.gradient_stops):
                offset = gradient_offsets[i]
                struct.pack_into('<f', binary, offset, stop.position)
                struct.pack_into('<f', binary, offset + 4, stop.a)
                logger.debug(f"Gradient stop {i} applied at 0x{offset:04x}: pos={stop.position}, alpha={stop.a}")
        else:
            logger.warning(f"Gradient stop count mismatch: {len(gradient_offsets)} vs {len(params.gradient_stops)}")

        return binary

    def _find_fill_color_offset(self, binary: bytes) -> Optional[int]:
        """Fill色のオフセットを探す"""
        # 0x0100付近を探索
        for offset in range(0x00f0, min(0x0150, len(binary) - 15), 4):
            try:
                r = struct.unpack('<f', binary[offset:offset+4])[0]
                g = struct.unpack('<f', binary[offset+4:offset+8])[0]
                b = struct.unpack('<f', binary[offset+8:offset+12])[0]
                a = struct.unpack('<f', binary[offset+12:offset+16])[0]

                # 0.0-1.0の範囲の妥当なRGBA
                if all(0.0 <= v <= 1.0 for v in [r, g, b, a]) and a > 0.01:
                    return offset
            except:
                pass
        return None

    def _find_stroke_width_offset(self, binary: bytes) -> Optional[int]:
        """ストローク幅のオフセットを探す"""
        # 0x0180付近を探索
        for offset in range(0x0170, min(0x01c0, len(binary) - 3), 4):
            try:
                val = struct.unpack('<f', binary[offset:offset+4])[0]
                # 妥当なストローク幅（0-500pt）
                if 0.0 <= val <= 500.0:
                    return offset
            except:
                pass
        return None

    def _find_shadow_xy_offsets(self, binary: bytes) -> List[dict]:
        """シャドウX,Yオフセットペアを探す"""
        shadow_block_start = 0x02dc
        if len(binary) <= shadow_block_start:
            return []

        xy_pairs = []
        for offset in range(shadow_block_start, len(binary) - 7, 4):
            try:
                x = struct.unpack('<f', binary[offset:offset+4])[0]
                y = struct.unpack('<f', binary[offset+4:offset+8])[0]

                if -50.0 <= x <= 50.0 and -50.0 <= y <= 50.0:
                    if abs(x - round(x)) < 0.1 and abs(y - round(y)) < 0.1:
                        if abs(x) > 0.5 or abs(y) > 0.5:
                            xy_pairs.append({'offset': offset, 'x': x, 'y': y})
            except:
                pass

        return xy_pairs

    def _find_gradient_stop_offsets(self, binary: bytes) -> List[int]:
        """グラデーションストップのオフセットを探す"""
        stops = []
        for offset in range(0, len(binary) - 7, 4):
            try:
                pos = struct.unpack('<f', binary[offset:offset+4])[0]
                alpha = struct.unpack('<f', binary[offset+4:offset+8])[0]

                # 妥当なPosition (0.0-1.0) とAlpha (0.0-1.0)
                if 0.0 <= pos <= 1.0 and 0.0 <= alpha <= 1.0:
                    stops.append(offset)
            except:
                pass

        return stops

    def _save_as_prtextstyle(self, binary: bytes, style_name: str, output_path: str):
        """バイナリをprtextstyleファイルとして保存"""
        # Base64エンコード
        b64 = base64.b64encode(binary).decode('ascii')

        # テンプレートファイルのXML構造を読み込んで再利用
        try:
            tree = ET.parse(self.template_path)
            root = tree.getroot()

            # すべてのStyleProjectItemを更新
            for style_item in root.findall('.//StyleProjectItem'):
                # スタイル名を更新
                name_elem = style_item.find('.//Name')
                if name_elem is not None:
                    name_elem.text = style_name

                # バイナリデータを更新
                for binary_elem in style_item.findall('.//StartKeyframeValue[@Encoding="base64"]'):
                    binary_elem.text = b64

            # XMLをファイルに書き込み
            tree.write(output_path, encoding='utf-8', xml_declaration=True)

        except Exception as e:
            logger.warning(f"Failed to use template structure: {e}, using simple structure")
            # フォールバック: シンプルな構造
            root = ET.Element('PremiereData', Version='3')
            style_project = ET.SubElement(root, 'StyleProjectItem', Class='StyleProjectItem', Version='1')
            name_elem = ET.SubElement(style_project, 'Name')
            name_elem.text = style_name

            component = ET.SubElement(style_project, 'Component', Class='VideoFilterComponent')
            param = ET.SubElement(component, 'Param', Index='0')
            arb_param = ET.SubElement(param, 'ArbVideoComponentParam')
            value_elem = ET.SubElement(arb_param, 'StartKeyframeValue', Encoding='base64')
            value_elem.text = b64

            tree = ET.ElementTree(root)
            ET.indent(tree, space='  ')
            tree.write(output_path, encoding='utf-8', xml_declaration=True)


def convert_prsl_style_to_prtextstyle_params(prsl_style) -> PrtextstyleParams:
    """
    PRSL Styleオブジェクトをprtextstyle paramsに変換

    Args:
        prsl_style: prsl_converter_modern.pyのStyleオブジェクト

    Returns:
        PrtextstyleParams
    """
    params = PrtextstyleParams()

    # Font
    params.font_family = prsl_style.font_family
    params.font_size = prsl_style.font_size

    # Fill
    if prsl_style.fill.is_gradient():
        params.fill_type = "gradient"
        params.gradient_angle = prsl_style.fill.gradient_angle
        params.gradient_stops = [
            GradientStop(
                position=stop.position,
                r=stop.r / 255.0,
                g=stop.g / 255.0,
                b=stop.b / 255.0,
                a=stop.a / 255.0
            )
            for stop in prsl_style.fill.gradient_stops
        ]
    else:
        params.fill_type = "solid"
        params.fill_r = prsl_style.fill.r / 255.0
        params.fill_g = prsl_style.fill.g / 255.0
        params.fill_b = prsl_style.fill.b / 255.0
        params.fill_a = prsl_style.fill.a / 255.0

    # Stroke
    if prsl_style.strokes:
        stroke = prsl_style.strokes[0]
        params.stroke_enabled = True
        params.stroke_width = stroke.width
        params.stroke_r = stroke.r / 255.0
        params.stroke_g = stroke.g / 255.0
        params.stroke_b = stroke.b / 255.0
        params.stroke_a = stroke.a / 255.0

    # Shadow
    if prsl_style.shadow.enabled:
        params.shadow_enabled = True
        params.shadow_x = prsl_style.shadow.offset_x
        params.shadow_y = prsl_style.shadow.offset_y
        params.shadow_blur = prsl_style.shadow.blur
        params.shadow_r = prsl_style.shadow.r / 255.0
        params.shadow_g = prsl_style.shadow.g / 255.0
        params.shadow_b = prsl_style.shadow.b / 255.0
        params.shadow_a = prsl_style.shadow.a / 255.0

    return params


if __name__ == "__main__":
    # テスト
    logging.basicConfig(level=logging.DEBUG)

    # テンプレート読み込み
    exporter = PrtextstyleTemplateExporter()

    # テストパラメータ
    params = PrtextstyleParams(
        fill_r=1.0, fill_g=0.0, fill_b=0.0, fill_a=1.0,
        shadow_enabled=True,
        shadow_x=5.0, shadow_y=5.0, shadow_blur=10.0
    )

    # エクスポート
    exporter.export(params, "Test Style", "test_export.prtextstyle")
    print("Test export completed: test_export.prtextstyle")
