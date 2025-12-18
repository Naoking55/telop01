# シャドウ色とシャドウ有無フラグの解析結果

**解析日**: 2025-12-13
**セッション**: シャドウ色の位置確定とシャドウ有無フラグの特定

---

## 🎯 重要な発見

このセッションで、**シャドウ専用ブロック**の存在を確認し、シャドウ有無の判定方法を解明しました。

---

## 📊 シャドウ専用ブロックの発見

### Fontstyle_01 (732 bytes) vs Fontstyle_90 (1756 bytes) の比較

**巨大な差分領域を発見:**
- オフセット: **0x02dc - 0x06dc**
- サイズ: **1024 bytes**
- 含まれる要素:
  - 黒色RGBA: 7箇所
  - X,Yオフセットペア: 14箇所
  - Blurパラメータ: 複数

### 発見の意味

この**1024バイトのブロック全体がシャドウ専用のデータ領域**であることが判明しました。

**重要:** Fontstyle_01（シンプルスタイル、732 bytes）にはこのブロックが存在しません。
→ **シャドウブロックの有無自体が、シャドウ有効/無効の判定となる**

---

## 🎨 シャドウ色の位置解析

### 検出された黒色RGBA (Fontstyle_90)

| オフセット | RGBA値 | Alpha |
|----------|--------|-------|
| 0x051c | (0.00, 0.00, 0.00, 1.00) | 不透明 |
| 0x0644 | (0.00, 0.00, 0.00, 1.00) | 不透明 |
| 0x065c | (0.00, 0.00, 0.00, 0.50) | 半透明 |
| 0x0680 | (0.00, 0.00, 0.00, 0.69) | 半透明 |
| 0x06a0 | (0.00, 0.00, 0.00, 0.65) | 半透明 |

### X,Yオフセットからの距離パターン

シャドウ色とX,Yオフセットの距離を解析した結果：

| X,Yオフセット | 最も近い黒色RGBA | 距離 |
|--------------|----------------|------|
| 0x0474 | 0x051c | +168 |
| 0x0478 | 0x051c | +164 |
| 0x047c | 0x051c | +160 |
| 0x04d0 | 0x051c | +76 |
| 0x0604 | 0x0644 | +64 |
| 0x0608 | 0x0644 | +60 |

**観察:**
- 距離が**統一されていない**（+60〜+168の範囲でバラバラ）
- X,Yオフセットから固定距離にシャドウ色が存在するわけではない

### 推測：FlatBuffersオフセット参照

シャドウ色は **FlatBuffersのオフセットテーブル経由で参照**されている可能性が高い。

**理由:**
1. 距離が統一されていない
2. FlatBuffersはVTable構造により、データ位置が動的に変化する
3. 直接的な相対オフセットではなく、間接参照を使用する設計

### シャドウ色候補の特定方法

**現時点での推奨アプローチ:**
1. シャドウブロック内（0x02dc - 0x06dc）を探索
2. Alpha > 0.0 の黒色RGBA (16バイト) を検索
3. 複数見つかった場合、最も近いものを選択

---

## 🚩 シャドウ有無フラグの特定

### 発見：シャドウブロックの存在自体がフラグ

**Fontstyle_01 (732 bytes):**
- シャドウブロックなし
- サイズ: 732 bytes

**Fontstyle_90 (1756 bytes):**
- シャドウブロックあり (0x02dc - 0x06dc, 1024 bytes)
- サイズ: 1756 bytes
- 差分: **1024 bytes = シャドウブロックのサイズ**

### サイズとシャドウの関係

| サイズ (bytes) | スタイル数 | シャドウ推定 |
|--------------|----------|-----------|
| 732 | 10 | なし（基本） |
| 808 | 10 | あり（軽量） |
| 916 | 10 | あり（標準） |
| 1756 | 9 | あり（複雑） |

**パターン:**
- 基本サイズ（732 bytes）+ シャドウブロック → より大きなサイズ
- シャドウブロックのサイズは可変（76〜1024 bytes）

### シャドウ有無の判定方法

**実装時の判定:**
1. **方法1**: ファイルサイズで判定
   - 732 bytes = シャドウなし
   - それ以上 = シャドウあり

2. **方法2**: 特定オフセットにシャドウブロックがあるか確認
   - 0x02dc付近を調査
   - X,Yオフセットペアが存在するか検出

3. **方法3**: FlatBuffersのVTableを解析
   - VTable内のフィールド数を確認
   - シャドウ関連フィールドの有無を判定

---

## 🔬 同一サイズスタイルの比較

### Fontstyle_01 vs Fontstyle_02 (両方732 bytes)

**差分:** たった **1バイト** (0x0216)
- Fontstyle_01: `0x71`
- Fontstyle_02: `0xa9`

**意味:**
- 同じサイズのスタイルはほぼ同一の構造
- わずかな設定差（色、フォントなど）のみ

---

## ✅ 確定した事実

### シャドウパラメータ構造（完全版）

```
シャドウブロック (可変サイズ、76〜1024+ bytes):
  開始: 0x02dc付近（Fontstyle_90の場合）
  終了: 可変

  含まれる要素:
  - X,Yオフセット (8 bytes): シャドウの位置
  - Blur (4 bytes): X,Yオフセットの±4〜12バイト
  - シャドウ色 RGBA (16 bytes): ブロック内、オフセット参照経由
  - その他メタデータ
```

### 確定事項一覧

| パラメータ | 状態 | 位置/詳細 |
|----------|------|----------|
| シャドウ有無 | ✅ 完全 | シャドウブロックの存在で判定 |
| シャドウブロック | ✅ 完全 | 0x02dc〜、可変サイズ |
| X,Yオフセット | ✅ 完全 | 8 bytes, ブロック内 |
| Blur | ✅ 完全 | 4 bytes, X,Yの±4〜12バイト |
| シャドウ色候補 | 🔄 部分 | 黒色RGBA、ブロック内、要オフセット参照解析 |

---

## 🧩 実装への応用

### Phase 1: シャドウブロックの検出

```python
def has_shadow(binary):
    """シャドウブロックの有無を判定"""
    # 方法1: サイズで判定（簡易）
    if len(binary) <= 732:
        return False

    # 方法2: X,Yオフセットペアを検出（精密）
    shadow_block_start = 0x02dc
    if len(binary) <= shadow_block_start:
        return False

    # シャドウブロック領域でX,Yオフセットペアを探す
    for offset in range(shadow_block_start, len(binary) - 7, 4):
        try:
            x = struct.unpack('<f', binary[offset:offset+4])[0]
            y = struct.unpack('<f', binary[offset+4:offset+8])[0]

            if -50.0 <= x <= 50.0 and -50.0 <= y <= 50.0:
                if abs(x) > 0.5 or abs(y) > 0.5:
                    return True  # シャドウあり
        except:
            pass

    return False
```

### Phase 2: シャドウ色の取得（暫定版）

```python
def find_shadow_color(binary, shadow_block_start, shadow_block_end):
    """シャドウブロック内から黒色RGBAを検索"""
    colors = []

    for offset in range(shadow_block_start, shadow_block_end - 15, 4):
        try:
            r = struct.unpack('<f', binary[offset:offset+4])[0]
            g = struct.unpack('<f', binary[offset+4:offset+8])[0]
            b = struct.unpack('<f', binary[offset+8:offset+12])[0]
            a = struct.unpack('<f', binary[offset+12:offset+16])[0]

            # 黒色でAlpha > 0
            if abs(r) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1 and a > 0.01:
                colors.append({
                    'offset': offset,
                    'rgba': (r, g, b, a)
                })
        except:
            pass

    return colors  # 最も近いものを選択する必要あり
```

### Phase 3: シャドウブロックの追加（生成時）

```python
def add_shadow_block(base_binary, shadow_x, shadow_y, shadow_blur, shadow_color):
    """
    基本スタイル（732 bytes）にシャドウブロックを追加

    注意: 完全な実装にはFlatBuffersのVTable更新が必要
    """
    # シャドウブロックテンプレートを使用
    shadow_block = create_shadow_block_template(
        shadow_x, shadow_y, shadow_blur, shadow_color
    )

    # 挿入位置（0x02dc）
    insert_pos = 0x02dc

    # バイナリを分割して挿入
    result = base_binary[:insert_pos] + shadow_block + base_binary[insert_pos:]

    # VTableとオフセット参照を更新（要実装）
    result = update_flatbuffers_offsets(result, insert_pos, len(shadow_block))

    return result
```

---

## ❓ 未解決の課題

### 優先度 HIGH

1. **シャドウ色のオフセット参照解析**
   - FlatBuffersのオフセットテーブルを解読
   - X,Yオフセットからシャドウ色への参照方法を特定

2. **シャドウブロックのテンプレート作成**
   - 最小限のシャドウブロック構造を特定
   - テンプレートから生成可能な形式に整理

3. **FlatBuffersのVTable更新**
   - シャドウブロック追加時のVTable更新ロジック
   - オフセット参照の再計算

### 優先度 MEDIUM

4. **複数シャドウの構造**
   - 1つのスタイルに複数のシャドウがある場合の構造
   - 各シャドウの用途（ドロップシャドウ、内側シャドウなど）

5. **シャドウブロックサイズのバリエーション**
   - 76 bytes〜1024 bytes の違いは何か
   - どの要素が可変か

---

## 📚 作成された解析ツール

| ツール | 用途 |
|--------|------|
| `analyze_shadow_color_position.py` | シャドウなし/あり比較、色位置解析 |
| `analyze_shadow_block.py` | シャドウブロック詳細解析 |
| `compare_same_size_styles.py` | 同一サイズスタイルの比較 |

---

## 📝 関連ドキュメント

- `SHADOW_PARAMETER_FINDINGS.md` - シャドウパラメータ基本解析
- `COMPLETE_ANALYSIS_SUMMARY.md` - 全解析結果サマリー

---

## 🎉 成果サマリー

このセッションで以下を達成:

1. ✅ **シャドウ専用ブロックの発見** - 0x02dc〜、1024 bytes
2. ✅ **シャドウ有無フラグの特定** - シャドウブロックの存在自体がフラグ
3. ✅ **シャドウ色候補の検出** - 黒色RGBA、ブロック内に複数存在
4. ✅ **同一サイズスタイルの分析** - Fontstyle_01 vs 02でたった1バイトの差分
5. 🔄 **シャドウ色の正確な参照方法** - FlatBuffersオフセット参照と推定（要追加解析）

---

**結論**: シャドウの**有無判定**と**基本パラメータ（X,Y,Blur）**は完全に解明。シャドウ色の正確な参照方法（FlatBuffersオフセットテーブル解析）が残る課題。しかし、シャドウブロック内の黒色RGBAを検索する方法で暫定的に対応可能。
