# PRSL → prtextstyle 変換ツール（モダン版）

Adobe Premiere Pro のレガシータイトル（PRSL）を、現行のエッセンシャルグラフィックス形式（prtextstyle）に変換するGUIツールです。

## ✨ 主な特徴

- **Python 3.8以上**で動作（3.12専用ではありません）
- **モダンなダークテーマGUI**（Tkinter標準ライブラリのみ）
- **リアルタイムプレビュー**（塗り・ストローク・シャドウ完全対応）
- **グラデーション対応**（2〜4色の線形グラデーション）
- **多重ストローク対応**（Legacy Title互換）
- **エラーハンドリング強化**

## 📋 必要な環境

### Python バージョン
- Python 3.8 〜 3.12（推奨: 3.10以上）

### 必須ライブラリ
```bash
pip install pillow numpy
```

### オプション（高速化）
```bash
pip install scipy  # ストローク描画の高速化（推奨）
```

## 🚀 使い方

### 1. 起動

```bash
python prsl_converter_modern.py
```

### 2. PRSLファイルを開く

メニューバー → **ファイル** → **PRSLを開く...**

または `Cmd+O` (Mac) / `Ctrl+O` (Windows/Linux)

### 3. スタイルを選択

左側のリストから変換したいスタイルをクリック

### 4. プレビュー確認

- 中央のプレビューエリアで見た目を確認
- 下部の「プレビューテキスト」で表示文字を変更可能

### 5. エクスポート

**📤 選択スタイルを書き出し** ボタンをクリック

→ `.prtextstyle` ファイルとして保存

## 🎨 GUI 改善点（旧版との比較）

| 項目 | 旧版 | 新版（モダン版） |
|------|------|------------------|
| GUI フレームワーク | PyQt5 / Tkinter 混在 | **Tkinter 統一** |
| デザイン | シンプル白背景 | **ダークテーマ + アクセントカラー** |
| フォント | 固定フォント | **システムフォント自動検出** |
| エラー表示 | コンソールのみ | **ステータスバー + ダイアログ** |
| プレビュー品質 | 基本的 | **高品質（Shadow/Gradient完全対応）** |

## 🔧 修正された問題点

### 🔴 重大な問題（修正済み）

1. ✅ **GUI フレームワーク混在** → Tkinter に統一
2. ✅ **未定義関数 `parse_prsl()`** → 実装追加
3. ✅ **属性名の不整合** (`gradient_stops` vs `stops`) → プロパティで統一
4. ✅ **dataclass の `copy()` メソッド** → 標準 `copy` モジュール使用

### 🟡 中程度の問題（修正済み）

5. ✅ **Shadow 属性の不整合** (`offset_x` vs `offsetX`) → `offset_x` に統一
6. ✅ **関数シグネチャ不一致** → `render()` の引数を統一
7. ✅ **BLOCK の実行順序** → クラス・関数を適切な順序で配置

### 🟢 改善（修正済み）

8. ✅ **dilate_mask のパフォーマンス** → scipy 使用（フォールバック付き）
9. ✅ **エラーハンドリング** → try-except + ログ出力
10. ✅ **Python 3.8 互換性** → 型ヒント調整

## 📁 ファイル構成

```
prsl_converter_modern.py    # メインプログラム（約800行、1ファイル完結）
├─ データクラス定義        # Style, Fill, Stroke, Shadow, GradientStop
├─ PRSL パーサー           # XML → Style オブジェクト
├─ レンダリングエンジン    # プレビュー画像生成
├─ prtextstyle エクスポーター
└─ モダンGUI               # Tkinter + ダークテーマ
```

## 🎯 使用例

### サンプル PRSL ファイル

```bash
# テスト用サンプル（sample_style.prsl）を使用
python prsl_converter_modern.py
# → ファイル → PRSLを開く → sample_style.prsl
```

### コマンドラインから直接エクスポート（開発予定）

```bash
# 将来的にバッチ処理モードも追加予定
python prsl_converter_modern.py --batch input_folder/ output_folder/
```

## ⚙️ カスタマイズ

### プレビューサイズを変更

`prsl_converter_modern.py` の冒頭で:

```python
DEFAULT_CANVAS_SIZE = (800, 250)  # → (1200, 400) など
```

### カラーテーマを変更

```python
COLORS = {
    'bg_dark': '#1e1e1e',      # ← 背景色をカスタマイズ
    'accent_blue': '#0e7afa',  # ← アクセントカラーを変更
    # ...
}
```

## 🐛 トラブルシューティング

### `ModuleNotFoundError: No module named 'PIL'`

```bash
pip install pillow
```

### `ModuleNotFoundError: No module named 'numpy'`

```bash
pip install numpy
```

### フォントが表示されない

- macOS: `/System/Library/Fonts/` にヒラギノフォントがあるか確認
- Windows: `C:\Windows\Fonts\` に游ゴシックがあるか確認
- Linux: `apt install fonts-noto-cjk` でフォントをインストール

### プレビューが遅い

```bash
# scipy をインストールすると高速化されます
pip install scipy
```

## 📝 開発情報

### バージョン履歴

- **v2.0.0** (2025-01-XX) - 完全リライト版
  - Python 3.8+ 対応
  - モダンGUI実装
  - 全問題修正

- **v1.0.0** (2025-01-XX) - 初版
  - 基本機能実装（問題あり）

### ライセンス

MIT License

### 作者

PRSL → prtextstyle Converter Project

## 🔗 関連リンク

- [Adobe Premiere Pro](https://www.adobe.com/products/premiere.html)
- [Python Pillow](https://pillow.readthedocs.io/)
- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)

---

**Enjoy Converting! 🎬✨**
