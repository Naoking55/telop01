#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRSL → prtextstyle 変換ツール（統合版）
====================================================================
FlatBuffers形式対応 + 解析結果を統合したバージョン

このファイルは prsl_converter_modern.py と prtextstyle_exporter.py を統合し、
実際のPremiere Pro 2025 prtextstyle形式で出力します。
"""

import sys
import os

# 既存のコンバーターをインポート
from prsl_converter_modern import (
    parse_prsl, Style, Fill, Stroke, Shadow,
    ModernStyleConverterGUI, logger, SPEC_VERSION, APP_TITLE
)

# 新しいエクスポーターをインポート
from prtextstyle_exporter import (
    PrtextstyleTemplateExporter,
    convert_prsl_style_to_prtextstyle_params
)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def export_prtextstyle_flatbuffers(style: Style, filepath: str, template_path: str = "prtextstyle/100 New Fonstyle.prtextstyle"):
    """
    prtextstyle ファイルとしてエクスポート（FlatBuffers形式）

    従来のTLV形式ではなく、実際のPremiere Pro 2025形式を使用

    Args:
        style: エクスポートするスタイル
        filepath: 出力ファイルパス
        template_path: ベーステンプレートのパス
    """
    try:
        # Styleオブジェクトをparamsに変換
        params = convert_prsl_style_to_prtextstyle_params(style)

        # テンプレートベースのエクスポーター
        exporter = PrtextstyleTemplateExporter(template_path)

        # エクスポート
        exporter.export(params, style.name, filepath)

        logger.info(f"✓ Exported (FlatBuffers): {os.path.basename(filepath)}")

    except Exception as e:
        logger.error(f"Export error: {e}")
        raise


class IntegratedStyleConverterGUI(ModernStyleConverterGUI):
    """
    統合版のスタイル変換GUI

    prsl_converter_modern.py の GUI を継承し、
    export メソッドだけ FlatBuffers 対応版に置き換え
    """

    def __init__(self):
        super().__init__()
        logger.info("✓ Integrated GUI initialized (FlatBuffers exporter)")

    def export_selected(self):
        """選択スタイルをエクスポート（FlatBuffers形式）"""
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
            # FlatBuffers形式でエクスポート
            export_prtextstyle_flatbuffers(self.current_style, filepath)

            messagebox.showinfo("成功", f"エクスポートしました:\n{os.path.basename(filepath)}")
            self.status_label.config(
                text=f"✓ エクスポート完了 (FlatBuffers): {os.path.basename(filepath)}",
                fg='#0fa968'  # COLORS['accent_green']
            )
        except Exception as e:
            import traceback
            messagebox.showerror("エラー", f"エクスポートに失敗しました:\n{e}")
            logger.error(f"Export error: {e}\n{traceback.format_exc()}")


def main():
    """メイン関数"""
    logger.info(f"Starting {APP_TITLE} v{SPEC_VERSION} (Integrated FlatBuffers)")
    logger.info(f"Python {sys.version}")

    try:
        app = IntegratedStyleConverterGUI()
        app.run()
    except Exception as e:
        import traceback
        logger.error(f"Fatal error: {e}\n{traceback.format_exc()}")
        messagebox.showerror("致命的エラー", f"アプリケーションの起動に失敗しました:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
