#!/usr/bin/env python3
"""
完全スタンドアロン版 PRSL→prtextstyle 変換ツール
依存関係: Python 3.8+ のみ（標準ライブラリのみ使用）
"""

import re
import base64
import xml.etree.ElementTree as ET
from dataclasses import dataclass
import tkinter as tk
from tkinter import filedialog, messagebox

# ============================================================================
# データクラス
# ============================================================================

@dataclass
class Fill:
    r: int
    g: int
    b: int

@dataclass
class Style:
    name: str
    fill: Fill

# ============================================================================
# PRSL解析（インライン実装）
# ============================================================================

def parse_prsl(prsl_path: str):
    """PRSLファイルを解析してスタイルリストを取得（Float値対応）"""
    tree = ET.parse(prsl_path)
    root = tree.getroot()

    styles = []
    for styleblock in root.findall('.//styleblock'):
        name = styleblock.get('name', 'Unknown')

        # Float値形式を探す: <solid_colour><all><red/green/blue>
        solid_colour = styleblock.find('.//solid_colour/all')

        if solid_colour is not None:
            # Float値（0.0-1.0）をByte値（0-255）に変換
            red_elem = solid_colour.find('red')
            green_elem = solid_colour.find('green')
            blue_elem = solid_colour.find('blue')

            if red_elem is not None and green_elem is not None and blue_elem is not None:
                r_float = float(red_elem.text)
                g_float = float(green_elem.text)
                b_float = float(blue_elem.text)

                r = int(r_float * 255)
                g = int(g_float * 255)
                b = int(b_float * 255)

                fill = Fill(r, g, b)
            else:
                fill = Fill(255, 255, 255)
        else:
            # 旧形式も試す: <fill><color rgb="...">
            fill_elem = styleblock.find('.//fill/color')
            if fill_elem is not None:
                rgb = fill_elem.get('rgb', '255 255 255')
                r, g, b = map(int, rgb.split())
                fill = Fill(r, g, b)
            else:
                fill = Fill(255, 255, 255)

        styles.append(Style(name=name, fill=fill))

    return styles

# ============================================================================
# 色変換ロジック
# ============================================================================

MARKER = b'\x02\x00\x00\x00\x41\x61'

def get_color_structure(r, g, b):
    """色構造を取得（どのRGB成分が255=skipか）"""
    structure = []
    stored = []

    if r == 255:
        structure.append('R=skip')
    else:
        structure.append('R=store')
        stored.append(('R', r))

    if g == 255:
        structure.append('G=skip')
    else:
        structure.append('G=store')
        stored.append(('G', g))

    if b == 255:
        structure.append('B=skip')
    else:
        structure.append('B=store')
        stored.append(('B', b))

    return ', '.join(structure), stored

def replace_color_bytes_in_binary(binary, target_r, target_g, target_b):
    """バイナリ内の色バイトをマーカーベース方式で置換"""
    binary = bytearray(binary)

    # マーカーを探す
    marker_pos = binary.find(MARKER)
    if marker_pos == -1:
        raise ValueError("マーカーが見つかりません")

    # ターゲット色の構造を取得
    target_structure, new_components = get_color_structure(target_r, target_g, target_b)

    # マーカー前のバイト数 = 保存される成分数
    num_bytes = len(new_components)

    # 色バイトを置き換え（マーカーの直前）
    for i in range(num_bytes):
        _, value = new_components[i]
        binary[marker_pos - num_bytes + i] = value

    return bytes(binary)

# ============================================================================
# 変換処理
# ============================================================================

def convert(log_func):
    """変換実行（ログ関数を受け取る）"""

    def log(msg):
        print(msg)
        log_func(msg)

    log("="*60)
    log("スタンドアロン版 PRSL→prtextstyle 変換ツール")
    log("="*60)

    # PRSLファイル選択
    prsl_file = filedialog.askopenfilename(
        title="PRSLファイルを選択",
        filetypes=[("PRSL files", "*.prsl"), ("All files", "*.*")]
    )
    if not prsl_file:
        log("\nキャンセルされました")
        return

    log(f"\n[1] PRSL: {prsl_file}")

    # 出力ファイル選択
    output_file = filedialog.asksaveasfilename(
        title="出力ファイル名を指定",
        defaultextension=".prtextstyle",
        filetypes=[("prtextstyle files", "*.prtextstyle"), ("All files", "*.*")]
    )
    if not output_file:
        log("\nキャンセルされました")
        return

    log(f"[2] 出力: {output_file}")

    # テンプレート選択
    template_file = filedialog.askopenfilename(
        title="テンプレートファイルを選択（手動変換済みprtextstyle）",
        filetypes=[("prtextstyle files", "*.prtextstyle"), ("All files", "*.*")]
    )
    if not template_file:
        log("\nキャンセルされました")
        return

    log(f"[3] テンプレート: {template_file}")

    try:
        # PRSL解析
        log(f"\n[4] PRSL解析中...")
        styles = parse_prsl(prsl_file)
        log(f"  ✓ {len(styles)} スタイル検出")

        # テンプレート読み込み
        log(f"\n[5] テンプレート読み込み中...")
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
        log(f"  ✓ {len(template_content)} chars ({len(template_content)/1024:.1f} KB)")

        # バイナリエントリ抽出
        log(f"\n[6] StartKeyframeValue エントリ抽出中...")
        pattern = r'(<StartKeyframeValue Encoding="base64" BinaryHash="[^"]+">)([A-Za-z0-9+/=\s]+)(</StartKeyframeValue>)'
        matches = list(re.finditer(pattern, template_content, re.DOTALL))
        log(f"  ✓ {len(matches)} エントリ検出")

        if len(matches) < len(styles):
            raise ValueError(f"テンプレートのスタイル数不足: {len(matches)} < {len(styles)}")

        # テンプレートバイナリ取得
        log(f"\n[7] テンプレートバイナリ取得中...")
        template_binaries = []
        for i, match in enumerate(matches):
            b64 = match.group(2).replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
            binary = base64.b64decode(b64)
            template_binaries.append(binary)
            log(f"  Template {i+1}: {len(binary)} bytes")

        # 変換処理
        log(f"\n[8] 変換処理:")
        conversions = []
        success_count = 0

        for i, style in enumerate(styles):
            r, g, b = style.fill.r, style.fill.g, style.fill.b
            log(f"  {i+1}/{len(styles)}: {style.name}")
            log(f"    RGB({r}, {g}, {b})")

            if i < len(template_binaries):
                try:
                    modified = replace_color_bytes_in_binary(template_binaries[i], r, g, b)
                    new_b64 = base64.b64encode(modified).decode('ascii')
                    conversions.append(new_b64)
                    success_count += 1
                    log(f"    ✓ 変換成功")
                except Exception as e:
                    log(f"    ✗ エラー: {e}")
                    conversions.append(None)
            else:
                conversions.append(None)

        log(f"\n[9] ファイル更新中...")
        log(f"  元のサイズ: {len(template_content)} chars")

        # 後ろから順に置換
        new_content = template_content
        for i in range(len(conversions) - 1, -1, -1):
            if conversions[i] is not None and i < len(matches):
                match = matches[i]
                new_b64 = conversions[i]
                new_content = (
                    new_content[:match.start(2)] +
                    new_b64 +
                    new_content[match.end(2):]
                )

        log(f"  新しいサイズ: {len(new_content)} chars ({len(new_content)/1024:.1f} KB)")

        # ファイル保存
        log(f"\n[10] ファイル保存中...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        import os
        final_size = os.path.getsize(output_file)
        log(f"  ✓ 保存完了")
        log(f"  ファイルサイズ: {final_size} bytes ({final_size/1024:.1f} KB)")

        # 結果判定
        log(f"\n{'='*60}")
        if final_size < 10000:
            log(f"⚠️ 警告: ファイルサイズが異常に小さい")
            log(f"{'='*60}")
            messagebox.showwarning(
                "警告",
                f"ファイルサイズが異常に小さい！\n\n"
                f"サイズ: {final_size} bytes\n"
                f"出力: {output_file}\n\n"
                f"期待値: 100KB以上"
            )
        else:
            log(f"✓✓✓ 変換完了！")
            log(f"{'='*60}")
            log(f"\n成功: {success_count}/{len(styles)} スタイル")
            log(f"出力: {output_file}")
            log(f"サイズ: {final_size/1024:.1f} KB")

            messagebox.showinfo(
                "変換完了",
                f"変換成功！\n\n"
                f"成功: {success_count}/{len(styles)} スタイル\n"
                f"出力: {output_file}\n"
                f"サイズ: {final_size/1024:.1f} KB\n\n"
                f"Premiere Proで読み込んでテストしてください！"
            )

    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        log(f"\n✗✗✗ エラー発生:")
        log(error_msg)
        messagebox.showerror("エラー", f"変換失敗:\n\n{error_msg}")

# ============================================================================
# GUI
# ============================================================================

def main():
    """メイン関数"""
    root = tk.Tk()
    root.title("PRSL→prtextstyle 変換ツール (スタンドアロン版)")
    root.geometry("800x600")

    # ログ表示エリア
    log_frame = tk.Frame(root, padx=10, pady=10)
    log_frame.pack(fill=tk.BOTH, expand=True)

    log_label = tk.Label(log_frame, text="ログ:", anchor='w')
    log_label.pack(anchor='w')

    log_text = tk.Text(log_frame, wrap=tk.WORD, font=('Courier', 10))
    log_text.pack(fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(log_text)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_text.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=log_text.yview)

    def log_to_gui(msg):
        log_text.insert(tk.END, msg + '\n')
        log_text.see(tk.END)
        root.update()

    # 変換ボタン
    def start_conversion():
        log_text.delete(1.0, tk.END)
        convert(log_to_gui)

    button_frame = tk.Frame(root, padx=10, pady=10)
    button_frame.pack()

    convert_btn = tk.Button(
        button_frame,
        text="🎬 変換開始",
        command=start_conversion,
        font=('Arial', 14, 'bold'),
        bg='#4CAF50',
        fg='white',
        padx=20,
        pady=10
    )
    convert_btn.pack()

    # 説明
    info_text = (
        "使い方:\n"
        "1. 「変換開始」ボタンをクリック\n"
        "2. PRSLファイルを選択\n"
        "3. 出力ファイル名を指定\n"
        "4. テンプレートファイルを選択\n"
        "5. 変換完了！"
    )
    info_label = tk.Label(root, text=info_text, justify=tk.LEFT, fg='gray')
    info_label.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
