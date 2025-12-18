#!/usr/bin/env python3
"""
PRSL→prtextstyle 変換ツール GUI版 v3.0
====================================================================
機能:
- ✅ 単色対応（100%精度）
- ✅ グラデーション対応（4色グラデーション）
- ✅ シャドウ対応（ぼかし・色）
- ✅ 無制限のスタイル数（テンプレート循環利用）
- ✅ Float値精密変換（切り捨て方式）

使い方:
1. PRSLファイルを選択
2. テンプレートprtextstyleを選択（例: 10styles.prtextstyle）
3. 出力先を選択
4. 変換実行
"""

import sys
import os

# COMPLETE_CONVERTER_v1.py の全機能をインポート
sys.path.insert(0, os.path.dirname(__file__))

# Import all functions from COMPLETE_CONVERTER_v1
from COMPLETE_CONVERTER_v1 import (
    parse_prsl,
    get_template_binaries,
    convert_style,
    create_prtextstyle_xml
)

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import threading

class ConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PRSL→prtextstyle 変換ツール v3.0")
        self.root.geometry("700x600")

        # Variables
        self.prsl_path = tk.StringVar()
        self.template_path = tk.StringVar()
        self.output_path = tk.StringVar()

        # デフォルトパス
        default_dir = "/home/user/telop01/10styles"
        self.template_path.set(f"{default_dir}/10styles.prtextstyle")

        self.create_widgets()

    def create_widgets(self):
        # Header
        header = tk.Label(
            self.root,
            text="PRSL→prtextstyle 変換ツール v3.0",
            font=("Arial", 16, "bold"),
            bg="#4CAF50",
            fg="white",
            pady=10
        )
        header.pack(fill=tk.X)

        # File selection frame
        file_frame = ttk.LabelFrame(self.root, text="ファイル選択", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=10)

        # PRSL file
        ttk.Label(file_frame, text="PRSLファイル:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.prsl_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="選択", command=self.select_prsl).grid(row=0, column=2)

        # Template file
        ttk.Label(file_frame, text="テンプレート:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.template_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(file_frame, text="選択", command=self.select_template).grid(row=1, column=2)

        # Output file
        ttk.Label(file_frame, text="出力先:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.output_path, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(file_frame, text="選択", command=self.select_output).grid(row=2, column=2)

        # Info frame
        info_frame = ttk.LabelFrame(self.root, text="対応機能", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        info_text = """
✅ 単色塗り (100%精度)
✅ 4色グラデーション対応
✅ シャドウ (ぼかし・色)
✅ 無制限のスタイル数
✅ Float値精密変換
        """
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack()

        # Convert button
        self.convert_btn = ttk.Button(
            self.root,
            text="変換実行",
            command=self.start_conversion,
            style="Accent.TButton"
        )
        self.convert_btn.pack(pady=10)

        # Progress
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10)

        # Log frame
        log_frame = ttk.LabelFrame(self.root, text="ログ", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            font=("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        """ログに追加"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def select_prsl(self):
        filename = filedialog.askopenfilename(
            title="PRSLファイルを選択",
            filetypes=[("PRSL files", "*.prsl"), ("All files", "*.*")]
        )
        if filename:
            self.prsl_path.set(filename)
            # 出力先を自動設定
            base = os.path.splitext(filename)[0]
            self.output_path.set(f"{base}_converted.prtextstyle")

    def select_template(self):
        filename = filedialog.askopenfilename(
            title="テンプレートprtextstyleファイルを選択",
            filetypes=[("prtextstyle files", "*.prtextstyle"), ("All files", "*.*")]
        )
        if filename:
            self.template_path.set(filename)

    def select_output(self):
        filename = filedialog.asksaveasfilename(
            title="出力先を選択",
            defaultextension=".prtextstyle",
            filetypes=[("prtextstyle files", "*.prtextstyle"), ("All files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)

    def start_conversion(self):
        """変換を別スレッドで実行"""
        if not self.prsl_path.get():
            messagebox.showerror("エラー", "PRSLファイルを選択してください")
            return
        if not self.template_path.get():
            messagebox.showerror("エラー", "テンプレートファイルを選択してください")
            return
        if not self.output_path.get():
            messagebox.showerror("エラー", "出力先を選択してください")
            return

        # ボタン無効化
        self.convert_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.log_text.delete(1.0, tk.END)

        # 別スレッドで変換
        thread = threading.Thread(target=self.run_conversion)
        thread.start()

    def run_conversion(self):
        """実際の変換処理"""
        try:
            prsl_path = self.prsl_path.get()
            template_path = self.template_path.get()
            output_path = self.output_path.get()

            self.log("="*60)
            self.log("PRSL→prtextstyle 変換開始")
            self.log("="*60)

            # PRSL解析
            self.log(f"\n[1] PRSL解析: {os.path.basename(prsl_path)}")
            styles = parse_prsl(prsl_path)
            self.log(f"  ✓ {len(styles)}スタイルを検出")

            # グラデーション数をカウント
            gradient_count = sum(1 for s in styles if s.fill.is_gradient)
            if gradient_count > 0:
                self.log(f"  ✓ グラデーション: {gradient_count}個")

            # テンプレート読み込み
            self.log(f"\n[2] テンプレート読み込み: {os.path.basename(template_path)}")
            template_binaries = get_template_binaries(template_path)
            self.log(f"  ✓ {len(template_binaries)}テンプレートを取得")

            if len(styles) > len(template_binaries):
                self.log(f"  ℹ️  {len(styles)}スタイル > {len(template_binaries)}テンプレート")
                self.log(f"  → テンプレート循環利用モード")

            # 変換処理
            self.log(f"\n[3] 変換処理:")
            converted_binaries = []

            for i, style in enumerate(styles):
                # テンプレート選択（循環利用）
                template_index = i % len(template_binaries)
                template = template_binaries[template_index]

                # 変換
                converted = convert_style(style, template)
                converted_binaries.append(converted)

                # ログ（10個ごと、またはグラデーションの場合）
                if (i + 1) % 10 == 0 or style.fill.is_gradient:
                    style_info = f"スタイル {i+1}: {style.name[:30]}"
                    if style.fill.is_gradient:
                        self.log(f"  {style_info} [グラデーション]")
                    else:
                        self.log(f"  {style_info}")

            self.log(f"  ✓ {len(converted_binaries)}スタイル変換完了")

            # XML生成
            self.log(f"\n[4] prtextstyleファイル生成:")
            create_prtextstyle_xml(styles, converted_binaries, output_path)
            self.log(f"  ✓ 保存完了: {os.path.basename(output_path)}")

            self.log(f"\n{'='*60}")
            self.log("✓✓✓ 変換完了！")
            self.log('='*60)
            self.log(f"成功: {len(converted_binaries)}/{len(styles)} スタイル")
            self.log(f"出力: {output_path}")

            # 成功メッセージ
            self.root.after(0, lambda: messagebox.showinfo(
                "完了",
                f"変換が完了しました！\n\n"
                f"スタイル数: {len(converted_binaries)}\n"
                f"グラデーション: {gradient_count}個\n"
                f"出力: {os.path.basename(output_path)}"
            ))

        except Exception as e:
            self.log(f"\n✗ エラー: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            self.root.after(0, lambda: messagebox.showerror("エラー", str(e)))

        finally:
            # UI復元
            self.root.after(0, self.restore_ui)

    def restore_ui(self):
        """UI状態を復元"""
        self.convert_btn.config(state=tk.NORMAL)
        self.progress.stop()

def main():
    root = tk.Tk()

    # スタイル設定
    style = ttk.Style()
    style.theme_use('clam')

    app = ConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
