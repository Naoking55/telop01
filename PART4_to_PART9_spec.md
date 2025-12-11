# PART4〜PART9 完全仕様書（PRSL → prtextstyle 変換）

---

# PART4：PRSL 仕様と抽出アルゴリズム

## 4.1 PRSL 基本構造
PRSL は Premiere のスタイルライブラリで、内部は PRPROJ と同様の XML 構造。
複数の `<StyleProjectItem>` を格納し、それぞれが 1 つのスタイルを保持。

- `<StyleProjectItem>`  
- `<Component>`  
- `<Param Index="0">` → `AE.ADBE Text` の base64 データ  

### 4.2 抽出手順
1. XML を読み込む  
2. `<StyleProjectItem>` を列挙  
3. `<Param Index="0">` の `<StartKeyframeValue Encoding="base64">` を取得  
4. Base64 をバイナリとして保存  

### 4.3 注意点
- PRSL は無制限にスタイルを含める  
- prtextstyle は 1 つの XML に複数スタイル格納可能だが、通常は 1スタイル=1ファイル  
- ツール側で「複数出力」「個別出力」を選択可能にする必要がある  

---

# PART5：Base64 ARB（AE.ADBE Text）仕様

## 5.1 構造
AE の「Arbitrary Data」は TLV（Tag-Length-Value）方式の連続ブロック。

```
[Tag][Length(4byte)][Value...]
```

Tag は Adobe 内部仕様だが複数のサンプルから推定可能。

## 5.2 主な Tag
| 機能 | Tag推定 | 説明 |
|------|---------|------|
| Solid Fill | 0x20 | 単色塗り |
| Gradient Fill | 0x21 | グラデ塗り |
| Gradient Stop | 0x22 | 48バイト固定 |
| Stroke | 0x30 | 単色ストローク |
| Shadow | 0x40 | ドロップシャドウ |
| Transform | 0x50 | 位置・回転・スケール |
| Font | 0x60 | フォント情報 |

---

# PART6：Gradient Stop（48バイト）完全仕様

Premiere のグラデーション定義で最重要部分。

```
00-03 : location (float32, 0〜1)
04-07 : midpoint (float32, 0〜1)
08-0B : R (float32, 0〜1)
0C-0F : G (float32, 0〜1)
10-13 : B (float32, 0〜1)
14-17 : A (float32, 0〜1)
18-2F : 固定24バイト（パディング）
```

全ての提供サンプルで一致 → **確定仕様**。

---

# PART7：EGP 制約と変換時の優先ルール

## 7.1 変換で捨てる機能
| 項目 | 再現可否 | 備考 |
|------|----------|------|
| 塗り不透明度 | ❌ | EGPに存在しない |
| 複数ストローク | ❌ | 単一のみ可 |
| 複数影 | ❌ | 1つのみ可 |
| 光沢 / メタリック | ❌ | グラデ近似で再現 |
| グラデストローク | ❌ | 単色にダウングレード |

## 7.2 変換時の優先順位
1. 可能な限り **視覚一致（90〜95%）** を目指す  
2. PRTL の構造は **中間JSONで正規化**  
3. prtextstyle は JSON → XML/TLV/Base64 に再構築  

---

# PART8：PRTL → prtextstyle 変換アルゴリズム（完全版）

## 8.1 変換パイプライン
```
PRTL → 中間JSON → prtextstyle(Base64+XML)
```

## 8.2 機能別変換ルール

### ★ 塗り（Fill）
- 単色 → そのまま変換  
- グラデ → Stop を float32 化して再構築  
- 光沢 → 3-stop グラデーションに近似  
- 塗り不透明度 → 廃止（100%固定）

### ★ ストローク
- 最外ストロークだけ採用  
- グラデストローク → 単色化  
- 太さは px→pt 換算（0.75pt/px）

### ★ 影（Shadow）
- 最も blur の大きい影を採用  
- offsetX/Y、color、opacity を float32 変換

### ★ フォント
- family / style / size / tracking  
→ 100%変換可

## 8.3 Base64 生成アルゴリズム（概要）
```
bin = TLV()
bin.add( fill_block )
bin.add( stroke_block )
bin.add( shadow_block )
bin.add( font_block )
bin.add( transform_block )
base64 = encode(bin)
xml = wrap(base64)
```

---

# PART9：PRSL → prtextstyle 変換ツール設計

## 9.1 UI機能
- PRSL読込  
- スタイル一覧表示  
- プレビュー生成（Canvas/Cairo）  
- 個別 or 一括書き出し  

## 9.2 出力オプション
- 1スタイル → 1ファイル  
- 複数スタイル → まとめた prtextstyle  

---

（以上 PART4〜PART9）
