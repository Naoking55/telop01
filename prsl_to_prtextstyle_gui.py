#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRSL → prtextstyle 変換ツール（1ファイル完結版）
====================================================================
Adobe Premiere PRSLファイルをPremiere Pro 2025 prtextstyle形式に変換

必要な依存関係:
- Python 3.8+
- Pillow (pip install Pillow)

使い方:
    python3 prsl_to_prtextstyle_gui.py
"""

import os
import sys
import base64
import struct
import math
import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
import logging
import traceback

# GUI
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
try:
    from PIL import ImageTk, Image
except ImportError:
    ImageTk = None
    Image = None

# ロギング設定
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ==============================================================================
# 定数
# ==============================================================================
APP_VERSION = "1.0.0"
APP_TITLE = "PRSL → prtextstyle 変換ツール"
DEFAULT_TEMPLATE = "prtextstyle/100 New Fonstyle.prtextstyle"

# カラースキーム
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
# データクラス定義
# ==============================================================================

@dataclass
class GradientStop:
    """グラデーションストップ"""
    position: float = 0.0
    midpoint: float = 0.5
    r: int = 255
    g: int = 255
    b: int = 255
    a: int = 255


@dataclass
class Fill:
    """塗り情報"""
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
    """ストローク情報"""
    width: float = 1.0
    r: int = 0
    g: int = 0
    b: int = 0
    a: int = 255


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


@dataclass
class Style:
    """スタイル情報"""
    name: str = "Unnamed Style"
    font_family: str = "Arial"
    font_size: float = 64.0
    bold: bool = False
    italic: bool = False
    fill: Fill = field(default_factory=Fill)
    strokes: List[Stroke] = field(default_factory=list)
    shadow: Shadow = field(default_factory=Shadow)
    opacity: float = 1.0


# ==============================================================================
# PRSL パーサー（軽量版）
# ==============================================================================

class PRSLParser:
    """PRSLファイルパーサー（stylelist形式対応）"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.styles: List[Style] = []

    def parse(self) -> List[Style]:
        """PRSLファイルを解析"""
        try:
            tree = ET.parse(self.filepath)
            root = tree.getroot()

            if root.tag == 'stylelist':
                # stylelist形式（新しいフォーマット）
                for styleblock in root.findall('styleblock'):
                    style = self._parse_styleblock(styleblock)
                    if style:
                        self.styles.append(style)
            else:
                logger.warning(f"Unsupported PRSL format: <{root.tag}>")

            logger.info(f"✓ Parsed {len(self.styles)} styles from {os.path.basename(self.filepath)}")
            return self.styles

        except Exception as e:
            logger.error(f"Parse error: {e}")
            traceback.print_exc()
            return []

    def _parse_styleblock(self, styleblock: ET.Element) -> Optional[Style]:
        """styleblockを解析"""
        name = styleblock.attrib.get('name', 'Unnamed Style')
        style = Style(name=name)

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
                    try:
                        style.font_size = float(size.text)
                    except ValueError:
                        pass

        # スタイルデータ
        style_data = styleblock.find('style_data')
        if style_data is not None:
            self._parse_fill(style_data, style)
            self._parse_shadow(style_data, style)

        return style

    def _parse_fill(self, style_data: ET.Element, style: Style):
        """Fill色を解析"""
        face = style_data.find('face')
        if face is None:
            return

        shader = face.find('shader')
        if shader is None:
            return

        colouring = shader.find('colouring')
        if colouring is None:
            return

        # タイプ確認
        type_elem = colouring.find('type')
        colour_type = 5  # デフォルト: solid
        if type_elem is not None and type_elem.text:
            try:
                colour_type = int(type_elem.text)
            except ValueError:
                pass

        if colour_type == 5:
            # 単色
            solid = colouring.find('solid_colour')
            if solid is not None:
                all_elem = solid.find('all')
                if all_elem is not None:
                    r = self._get_color_value(all_elem, 'red')
                    g = self._get_color_value(all_elem, 'green')
                    b = self._get_color_value(all_elem, 'blue')
                    a = self._get_color_value(all_elem, 'alpha')
                    style.fill = Fill(fill_type="solid", r=r, g=g, b=b, a=a)
        else:
            # グラデーション（簡易対応）
            two_colour = colouring.find('two_colour_ramp')
            if two_colour is not None:
                stops = []
                # Top color
                top = two_colour.find('top')
                if top is not None:
                    r = self._get_color_value(top, 'red')
                    g = self._get_color_value(top, 'green')
                    b = self._get_color_value(top, 'blue')
                    a = self._get_color_value(top, 'alpha')
                    stops.append(GradientStop(position=0.0, r=r, g=g, b=b, a=a))

                # Bottom color
                bottom = two_colour.find('bottom')
                if bottom is not None:
                    r = self._get_color_value(bottom, 'red')
                    g = self._get_color_value(bottom, 'green')
                    b = self._get_color_value(bottom, 'blue')
                    a = self._get_color_value(bottom, 'alpha')
                    stops.append(GradientStop(position=1.0, r=r, g=g, b=b, a=a))

                # Angle
                angle_elem = two_colour.find('angle')
                angle = 0.0
                if angle_elem is not None and angle_elem.text:
                    try:
                        angle = float(angle_elem.text)
                    except ValueError:
                        pass

                if stops:
                    style.fill = Fill(
                        fill_type="gradient",
                        gradient_stops=stops,
                        gradient_angle=angle
                    )

    def _parse_shadow(self, style_data: ET.Element, style: Style):
        """シャドウを解析"""
        shadow_elem = style_data.find('shadow')
        if shadow_elem is None:
            return

        # 有効/無効
        on_elem = shadow_elem.find('on')
        if on_elem is None or not on_elem.text:
            return

        if on_elem.text.strip().lower() != 'true':
            return

        # Blur
        softness = shadow_elem.find('softness')
        blur = 4.0
        if softness is not None and softness.text:
            try:
                blur = float(softness.text) / 10.0
            except ValueError:
                pass

        # Color
        colour = shadow_elem.find('colour')
        r, g, b, a = 0, 0, 0, 120
        if colour is not None:
            r = self._get_color_value(colour, 'red')
            g = self._get_color_value(colour, 'green')
            b = self._get_color_value(colour, 'blue')
            a = self._get_color_value(colour, 'alpha')

        # Offset
        offset = shadow_elem.find('offset')
        offset_x, offset_y = 2.0, 2.0
        if offset is not None:
            angle_elem = offset.find('angle')
            mag_elem = offset.find('magnitude')

            angle = 90.0
            magnitude = 5.0

            if angle_elem is not None and angle_elem.text:
                try:
                    angle = float(angle_elem.text)
                except ValueError:
                    pass

            if mag_elem is not None and mag_elem.text:
                try:
                    magnitude = float(mag_elem.text)
                except ValueError:
                    pass

            rad = math.radians(angle)
            offset_x = magnitude * math.cos(rad)
            offset_y = -magnitude * math.sin(rad)

        style.shadow = Shadow(
            enabled=True,
            offset_x=offset_x,
            offset_y=offset_y,
            blur=blur,
            r=r, g=g, b=b, a=a
        )

    def _get_color_value(self, elem: ET.Element, name: str) -> int:
        """色要素の値を取得（0-255）"""
        comp = elem.find(name)
        if comp is not None and comp.text:
            try:
                # 0.0-1.0 → 0-255
                return int(float(comp.text) * 255)
            except ValueError:
                pass
        return 255 if name == 'alpha' else 0


# ==============================================================================
# prtextstyle エクスポーター（FlatBuffers対応）
# ==============================================================================

@dataclass
class PrtextstyleParams:
    """prtextstyle パラメータ"""
    font_family: str = "Arial"
    font_size: float = 64.0
    fill_type: str = "solid"
    fill_r: float = 1.0
    fill_g: float = 1.0
    fill_b: float = 1.0
    fill_a: float = 1.0
    gradient_stops: List[GradientStop] = None
    gradient_angle: float = 0.0
    stroke_enabled: bool = False
    stroke_width: float = 0.0
    stroke_r: float = 0.0
    stroke_g: float = 0.0
    stroke_b: float = 0.0
    stroke_a: float = 1.0
    shadow_enabled: bool = False
    shadow_x: float = 0.0
    shadow_y: float = 0.0
    shadow_blur: float = 0.0
    shadow_r: float = 0.0
    shadow_g: float = 0.0
    shadow_b: float = 0.0
    shadow_a: float = 0.5


class PrtextstyleExporter:
    """prtextstyle エクスポーター（テンプレートベース）"""

    def __init__(self, template_path: str = DEFAULT_TEMPLATE):
        self.template_path = template_path
        self.template_binary = None
        self._load_template()

    def _load_template(self):
        """テンプレートを読み込み"""
        if not os.path.exists(self.template_path):
            logger.warning(f"Template not found: {self.template_path}")
            # 最小限のテンプレート（732バイト）
            self.template_binary = b'\x00' * 732
            return

        try:
            tree = ET.parse(self.template_path)
            root = tree.getroot()

            # 最初のStyleProjectItemからバイナリを取得
            for style_item in root.findall('.//StyleProjectItem'):
                component_ref_elem = style_item.find('.//Component[@ObjectRef]')
                if component_ref_elem is None:
                    continue

                component_ref = component_ref_elem.get('ObjectRef')
                vfc = root.find(f".//VideoFilterComponent[@ObjectID='{component_ref}']")
                if vfc is None:
                    continue

                first_param_ref = vfc.find(".//Param[@Index='0']")
                if first_param_ref is None:
                    continue

                param_obj_ref = first_param_ref.get('ObjectRef')
                arb_param = root.find(f".//ArbVideoComponentParam[@ObjectID='{param_obj_ref}']")
                if arb_param is None:
                    continue

                binary_elem = arb_param.find(".//StartKeyframeValue[@Encoding='base64']")
                if binary_elem is not None and binary_elem.text:
                    self.template_binary = base64.b64decode(binary_elem.text.strip())
                    logger.info(f"Template loaded: {len(self.template_binary)} bytes")
                    break

        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            self.template_binary = b'\x00' * 732

    def export(self, params: PrtextstyleParams, style_name: str, output_path: str):
        """prtextstyleファイルをエクスポート"""
        # テンプレートをコピー
        binary = bytearray(self.template_binary)

        # パラメータ適用
        binary = self._apply_fill(binary, params)
        binary = self._apply_shadow(binary, params)

        # XMLに保存
        self._save_as_prtextstyle(bytes(binary), style_name, output_path)
        logger.info(f"✓ Exported: {output_path} ({len(binary)} bytes)")

    def _apply_fill(self, binary: bytearray, params: PrtextstyleParams) -> bytearray:
        """Fill色を適用"""
        if params.fill_type != "solid":
            return binary

        # Fill色の位置を探す（0x0100付近）
        for offset in range(0x00f0, min(0x0150, len(binary) - 15), 4):
            try:
                r = struct.unpack('<f', binary[offset:offset+4])[0]
                g = struct.unpack('<f', binary[offset+4:offset+8])[0]
                b = struct.unpack('<f', binary[offset+8:offset+12])[0]
                a = struct.unpack('<f', binary[offset+12:offset+16])[0]

                if all(0.0 <= v <= 1.0 for v in [r, g, b, a]) and a > 0.01:
                    # 発見！置き換え
                    struct.pack_into('<f', binary, offset, params.fill_r)
                    struct.pack_into('<f', binary, offset + 4, params.fill_g)
                    struct.pack_into('<f', binary, offset + 8, params.fill_b)
                    struct.pack_into('<f', binary, offset + 12, params.fill_a)
                    logger.debug(f"Fill color applied at 0x{offset:04x}")
                    break
            except:
                pass

        return binary

    def _apply_shadow(self, binary: bytearray, params: PrtextstyleParams) -> bytearray:
        """シャドウを適用"""
        if not params.shadow_enabled:
            return binary

        shadow_block_start = 0x02dc
        if len(binary) <= shadow_block_start:
            logger.warning("Shadow block not available (file too small)")
            return binary

        # Shadow X,Y の位置を探す
        for offset in range(shadow_block_start, len(binary) - 7, 4):
            try:
                x = struct.unpack('<f', binary[offset:offset+4])[0]
                y = struct.unpack('<f', binary[offset+4:offset+8])[0]

                if -50.0 <= x <= 50.0 and -50.0 <= y <= 50.0:
                    if abs(x - round(x)) < 0.1 and abs(y - round(y)) < 0.1:
                        if abs(x) > 0.5 or abs(y) > 0.5:
                            # 発見！置き換え
                            struct.pack_into('<f', binary, offset, params.shadow_x)
                            struct.pack_into('<f', binary, offset + 4, params.shadow_y)
                            logger.debug(f"Shadow X,Y applied at 0x{offset:04x}")

                            # Blur を探す（X,Yの±4-12バイト）
                            for delta in [-12, -8, -4, 4, 8, 12]:
                                blur_offset = offset + delta
                                if 0 <= blur_offset + 4 <= len(binary):
                                    try:
                                        val = struct.unpack('<f', binary[blur_offset:blur_offset+4])[0]
                                        if 0 <= val <= 100:
                                            struct.pack_into('<f', binary, blur_offset, params.shadow_blur)
                                            logger.debug(f"Shadow blur applied at 0x{blur_offset:04x}")
                                            return binary
                                    except:
                                        pass
                            break
            except:
                pass

        return binary

    def _save_as_prtextstyle(self, binary: bytes, style_name: str, output_path: str):
        """XMLとして保存"""
        b64 = base64.b64encode(binary).decode('ascii')

        # テンプレートのXML構造を保持
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

            tree.write(output_path, encoding='utf-8', xml_declaration=True)

        except Exception as e:
            logger.warning(f"Failed to use template structure: {e}")
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


def style_to_params(style: Style) -> PrtextstyleParams:
    """StyleをPrtextstyleParamsに変換"""
    params = PrtextstyleParams()

    params.font_family = style.font_family
    params.font_size = style.font_size

    # Fill
    if style.fill.is_gradient():
        params.fill_type = "gradient"
        params.gradient_angle = style.fill.gradient_angle
        params.gradient_stops = style.fill.gradient_stops
    else:
        params.fill_type = "solid"
        params.fill_r = style.fill.r / 255.0
        params.fill_g = style.fill.g / 255.0
        params.fill_b = style.fill.b / 255.0
        params.fill_a = style.fill.a / 255.0

    # Stroke
    if style.strokes:
        stroke = style.strokes[0]
        params.stroke_enabled = True
        params.stroke_width = stroke.width
        params.stroke_r = stroke.r / 255.0
        params.stroke_g = stroke.g / 255.0
        params.stroke_b = stroke.b / 255.0
        params.stroke_a = stroke.a / 255.0

    # Shadow
    if style.shadow.enabled:
        params.shadow_enabled = True
        params.shadow_x = style.shadow.offset_x
        params.shadow_y = style.shadow.offset_y
        params.shadow_blur = style.shadow.blur
        params.shadow_r = style.shadow.r / 255.0
        params.shadow_g = style.shadow.g / 255.0
        params.shadow_b = style.shadow.b / 255.0
        params.shadow_a = style.shadow.a / 255.0

    return params


# ==============================================================================
# GUI
# ==============================================================================

class ConverterGUI:
    """変換ツールGUI"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_TITLE} v{APP_VERSION}")
        self.root.geometry("900x600")

        self.styles: List[Style] = []
        self.current_style: Optional[Style] = None

        self._setup_styles()
        self._build_ui()

        logger.info("✓ GUI initialized")

    def _setup_styles(self):
        """ttk スタイル設定"""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass

        style.configure('Title.TLabel',
                       background=COLORS['bg_dark'],
                       foreground=COLORS['fg_primary'],
                       font=('Helvetica', 14, 'bold'))

        self.root.configure(bg=COLORS['bg_dark'])

    def _build_ui(self):
        """UI構築"""
        # メインコンテナ
        main = tk.Frame(self.root, bg=COLORS['bg_dark'])
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # タイトル
        title = tk.Label(
            main,
            text=APP_TITLE,
            bg=COLORS['bg_dark'],
            fg=COLORS['fg_primary'],
            font=('Helvetica', 16, 'bold')
        )
        title.pack(pady=(0, 10))

        # ボタンエリア
        btn_frame = tk.Frame(main, bg=COLORS['bg_dark'])
        btn_frame.pack(fill="x", pady=(0, 10))

        load_btn = tk.Button(
            btn_frame,
            text="📂 PRSLファイルを開く",
            command=self.load_prsl,
            bg=COLORS['accent_blue'],
            fg=COLORS['fg_primary'],
            font=('Helvetica', 12, 'bold'),
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        load_btn.pack(side="left", padx=(0, 10))

        export_all_btn = tk.Button(
            btn_frame,
            text="💾 すべて書き出し",
            command=self.export_all,
            bg=COLORS['accent_green'],
            fg=COLORS['fg_primary'],
            font=('Helvetica', 12, 'bold'),
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        export_all_btn.pack(side="left")

        # スタイル一覧
        list_frame = tk.Frame(main, bg=COLORS['bg_medium'], bd=2, relief="solid")
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        list_label = tk.Label(
            list_frame,
            text="スタイル一覧",
            bg=COLORS['bg_medium'],
            fg=COLORS['fg_primary'],
            font=('Helvetica', 12, 'bold')
        )
        list_label.pack(pady=5)

        scrollbar = tk.Scrollbar(list_frame, bg=COLORS['bg_medium'])
        scrollbar.pack(side="right", fill="y")

        self.style_listbox = tk.Listbox(
            list_frame,
            bg=COLORS['bg_light'],
            fg=COLORS['fg_primary'],
            selectbackground=COLORS['accent_blue'],
            selectforeground=COLORS['fg_primary'],
            font=('Menlo', 11),
            bd=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        self.style_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.config(command=self.style_listbox.yview)

        self.style_listbox.bind("<<ListboxSelect>>", self.on_style_select)
        self.style_listbox.bind("<Double-Button-1>", lambda e: self.export_selected())

        # ステータスバー
        self.status_label = tk.Label(
            main,
            text="PRSLファイルを開いてください",
            bg=COLORS['bg_dark'],
            fg=COLORS['fg_secondary'],
            font=('Helvetica', 10),
            anchor="w"
        )
        self.status_label.pack(fill="x")

    def load_prsl(self):
        """PRSLファイルを読み込み"""
        filepath = filedialog.askopenfilename(
            title="PRSLファイルを選択",
            filetypes=[("PRSL Files", "*.prsl"), ("All Files", "*.*")]
        )

        if not filepath:
            return

        try:
            parser = PRSLParser(filepath)
            self.styles = parser.parse()

            self.style_listbox.delete(0, tk.END)

            for i, style in enumerate(self.styles):
                self.style_listbox.insert(tk.END, f"{i+1:02d}  {style.name}")

            self.status_label.config(
                text=f"✓ {len(self.styles)} スタイルを読み込みました: {os.path.basename(filepath)}",
                fg=COLORS['accent_green']
            )

        except Exception as e:
            messagebox.showerror("エラー", f"PRSLファイルの読み込みに失敗しました:\n{e}")
            logger.error(f"Load error: {e}")

    def on_style_select(self, event=None):
        """スタイル選択時"""
        sel = self.style_listbox.curselection()
        if not sel:
            return

        index = sel[0]
        self.current_style = self.styles[index]

        # スタイル情報を表示
        info = f"選択中: {self.current_style.name} | "
        info += f"Fill: RGB({self.current_style.fill.r},{self.current_style.fill.g},{self.current_style.fill.b}) | "
        if self.current_style.shadow.enabled:
            info += f"Shadow: ON (Blur={self.current_style.shadow.blur:.1f})"
        else:
            info += "Shadow: OFF"

        self.status_label.config(text=info, fg=COLORS['accent_blue'])

    def export_selected(self):
        """選択中のスタイルを書き出し"""
        if not self.current_style:
            messagebox.showwarning("警告", "スタイルが選択されていません")
            return

        filepath = filedialog.asksaveasfilename(
            title="prtextstyle として保存",
            defaultextension=".prtextstyle",
            filetypes=[("prtextstyle Files", "*.prtextstyle"), ("All Files", "*.*")],
            initialfile=f"{self.current_style.name}.prtextstyle"
        )

        if not filepath:
            return

        try:
            exporter = PrtextstyleExporter()
            params = style_to_params(self.current_style)
            exporter.export(params, self.current_style.name, filepath)

            messagebox.showinfo("成功", f"エクスポートしました:\n{os.path.basename(filepath)}")
            self.status_label.config(
                text=f"✓ エクスポート完了: {os.path.basename(filepath)}",
                fg=COLORS['accent_green']
            )

        except Exception as e:
            messagebox.showerror("エラー", f"エクスポートに失敗しました:\n{e}")
            logger.error(f"Export error: {e}")

    def export_all(self):
        """すべてのスタイルを一括書き出し"""
        if not self.styles:
            messagebox.showwarning("警告", "スタイルが読み込まれていません")
            return

        directory = filedialog.askdirectory(title="保存先フォルダを選択")
        if not directory:
            return

        try:
            exporter = PrtextstyleExporter()
            success_count = 0

            for style in self.styles:
                filename = f"{style.name.replace('/', '_').replace(' ', '_')}.prtextstyle"
                filepath = os.path.join(directory, filename)

                params = style_to_params(style)
                exporter.export(params, style.name, filepath)
                success_count += 1

            messagebox.showinfo("成功", f"{success_count}個のスタイルをエクスポートしました")
            self.status_label.config(
                text=f"✓ {success_count}個のスタイルをエクスポート完了",
                fg=COLORS['accent_green']
            )

        except Exception as e:
            messagebox.showerror("エラー", f"エクスポートに失敗しました:\n{e}")
            logger.error(f"Export error: {e}")

    def run(self):
        """GUIを起動"""
        self.root.mainloop()


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """メイン関数"""
    logger.info(f"Starting {APP_TITLE} v{APP_VERSION}")
    logger.info(f"Python {sys.version}")

    try:
        app = ConverterGUI()
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()
        messagebox.showerror("致命的エラー", f"アプリケーションの起動に失敗しました:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
