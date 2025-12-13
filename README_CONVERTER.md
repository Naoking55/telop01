# PRSL → prtextstyle 変換ツール

## 📄 ファイル

**`prsl_to_prtextstyle_gui.py`** - 1ファイル完結のGUI変換プログラム

- **行数**: 約880行
- **依存関係**: Python 3.8+ + Pillow
- **GUI**: Tkinter（Python標準ライブラリ）

## 🚀 使い方

### 1. 依存関係のインストール

```bash
pip install Pillow
```

### 2. プログラムの起動

```bash
python3 prsl_to_prtextstyle_gui.py
```

### 3. GUIでの操作

1. **「📂 PRSLファイルを開く」** ボタンをクリック
2. 変換したいPRSLファイルを選択
3. スタイル一覧が表示されます
4. 変換方法を選択：
   - **個別変換**: スタイルをダブルクリック、または選択後に保存
   - **一括変換**: **「💾 すべて書き出し」** ボタンをクリック

## ✨ 機能

### 対応している変換
- ✅ **Fill色**（単色）
- ✅ **Shadow**（X, Y, Blur, Color）
- ⚠️ **Gradient**（2色グラデーション、部分対応）
- ⚠️ **Stroke**（部分対応）

### 出力フォーマット
- ✅ Premiere Pro 2025 prtextstyle形式（FlatBuffers）
- ✅ テンプレートベース変換で完全互換
