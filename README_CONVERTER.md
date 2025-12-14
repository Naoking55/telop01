# PRSL → prtextstyle 変換ツール

Adobe Premiere Pro用のレガシーPRSLファイルを最新のprtextstyle形式に変換するツールです。

## 📄 利用可能なプログラム

### 1. **`FINAL_prsl_converter.py`** - CLI版（推奨・最新）

**完全自動テンプレートマッチング方式**

- **動作確認**: ✅ 10/10 スタイルで変換成功
- **依存関係**: Python 3.8+ のみ（追加パッケージ不要）
- **方式**: テンプレートマッチング（完全自動）
- **対応**: Fill色（単色）の完全変換

```bash
python3 FINAL_prsl_converter.py [prsl_file] [output_file] [template_file]
```

**例:**
```bash
python3 FINAL_prsl_converter.py /tmp/10styles.prsl output.prtextstyle /tmp/10styles.prtextstyle
```

### 2. **`prsl_to_prtextstyle_gui.py`** - GUI版（高機能）v2.0 ✨NEW

**1ファイル完結のGUI変換プログラム（マーカーベース方式対応）**

- **バージョン**: v2.0（2024-12-14更新）
- **行数**: 約920行
- **依存関係**: Python 3.8+ + Pillow
- **GUI**: Tkinter（Python標準ライブラリ）
- **Fill色変換**: マーカーベース方式（FINAL_prsl_converter.py と同じ）
- **対応**: Fill色、Shadow、Gradient（部分）、Stroke（部分）

```bash
pip install Pillow
python3 prsl_to_prtextstyle_gui.py
```

**GUIでの操作:**
1. **「📂 PRSLファイルを開く」** ボタンをクリック
2. 変換したいPRSLファイルを選択
3. スタイル一覧が表示されます
4. 変換方法を選択：
   - **個別変換**: スタイルをダブルクリック、または選択後に保存
   - **一括変換**: **「💾 すべて書き出し」** ボタンをクリック

## 🎯 どちらを使うべきか？

| 用途 | おすすめ | 理由 |
|------|---------|------|
| Fill色のみの変換 | **FINAL_prsl_converter.py** | 依存関係なし、動作確認済み |
| Gradient/Shadow対応 | **prsl_to_prtextstyle_gui.py** | 高機能、ビジュアル確認可能 |
| バッチ処理/自動化 | **FINAL_prsl_converter.py** | コマンドライン対応 |
| 初心者向け | **prsl_to_prtextstyle_gui.py** | GUI操作が簡単 |

## ✨ 機能比較

### FINAL_prsl_converter.py（CLI版）
- ✅ **Fill色**（単色）- 完全対応、テスト済み
- ✅ テンプレートマッチング方式
- ✅ 10/10 スタイルで変換成功を確認
- ✅ 追加パッケージ不要

### prsl_to_prtextstyle_gui.py（GUI版 v2.0）
- ✅ **Fill色**（単色）- **マーカーベース方式、CLI版と同じロジック**
- ✅ **Shadow**（X, Y, Blur, Color）
- ⚠️ **Gradient**（2色グラデーション、部分対応）
- ⚠️ **Stroke**（部分対応）
- ✅ フォールバック機能付き

### 共通
- ✅ Premiere Pro 2025 prtextstyle形式（FlatBuffers）
- ✅ テンプレートベース変換で完全互換
