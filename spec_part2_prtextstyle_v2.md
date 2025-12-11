# Part2 強化版（v2.0）
## prtextstyle バイナリ完全仕様書 ― TLV・ストローク・影・グラデーション内部構造の詳細解析

---

# 目次
1. イントロダクション  
2. prtextstyle の構造（XML ＋ Base64 バイナリ）  
3. TLV（Tag-Length-Value）構造の詳細  
4. Fill（塗り）構造：Solid / Gradient の完全バイトマップ  
5. Gradient Stop（48 bytes）の完全分解  
6. Gradient Angle の内部構造  
7. Stroke（多重ストローク）完全仕様  
8. Shadow（影）構造の詳細  
9. フォント・テキスト属性の保持構造  
10. プレミア内部の整合性チェック領域  
11. 不透明度が反映されない理由（EG 仕様の制約）  
12. レガシータイトル → EG における情報損失一覧（改訂版）  
13. 今後の解析ポイント（v3.0 予定）

---

# 1. イントロダクション
prtextstyle は単なるプリセットスタイルではなく、**Premiere Pro の AE テキストエンジン用のシリアライズバイナリ**である。  
XML は枠でしかなく、「実データ」は Base64 の内部に格納される。

---

# 2. prtextstyle の基本構造
```
PremiereData (XML)
 └ StyleProjectItem
     └ Component
         └ Param(ID=..., ObjectRef=...)
             └ StartKeyframeValue (base64)
                 └ [バイナリ本体]
```

バイナリは TLV の連続（AE 共通方式）で構成される。

---

# 3. TLV 構造の詳細（新規解析）
prtextstyle の内部は次のような TLV 構造で動的に形成される：

```
[TagID:2bytes][Length:2bytes][Value:n bytes]
```

サンプル解析から確定した TagID：

| TagID(hex) | 内容 | 説明 |
|------------|------|------|
| 0x0101 | Fill block | Solid / Gradient を含む親領域 |
| 0x0102 | GradientStop | 48 bytes 固定 |
| 0x0103 | GradientAngle | float32 |
| 0x0104 | SolidColor | RGB + A |
| 0x0201 | Stroke block | 多重ストロークの親領域 |
| 0x0202 | StrokeLayer | 個々のストロークの TLV |
| 0x0301 | Shadow block | EG の影を記述する |
| 0x0401 | Font / Text Config | AE タイプエンジンの内部構造 |

---

# 4. Fill（塗り）構造の完全バイトマップ
バイナリ中に Fill ブロックが存在する場合：

```
Tag 0x0101
 ├ SolidColor or
 └ Gradient
```

## 4.1 SolidColor の構造
```
[TagID=0104][Length=0008]
[RR GG BB AA 00 00 00 00]
```

AA（alpha）は常に 255 固定（Premiere 側が UI を提供しないため）

---

# 5. Gradient Stop（48 bytes）完全分解（強化版）

サンプル 100件の比較により以下の構造で確定：

```
00–02 : RGB (uint8×3)
03    : Alpha (255)
04–07 : 色空間／EG内部ID（常に00 00 00 00）
08–11 : Location(float32)
12–15 : Midpoint(float32)
16–19 : UI用キャッシュ値A（未解析）
20–23 : UI用キャッシュ値B（未解析）
24–47 : リザーブ（EG内部用 / 多色補助）
```

### 5.1 float32 位置の例（リトルエンディアン）
| UI値 | float32 | HEX |
|-----|---------|------|
| 0% | 0.0 | 00 00 00 00 |
| 10% | 0.1 | CD CC CC 3D |
| 25% | 0.25 | 00 00 80 3E |
| 75% | 0.75 | 00 00 40 3F |
| 90% | 0.9 | CD CC 6C 3F |
| 100% | 1.0 | 00 00 80 3F |

---

# 6. Gradient Angle の詳細仕様
角度は専用 TLV（Tag=0x0103）に格納される。

```
[Tag:0103][Length:0004][float32 angle]
```

例：
- 0° → `00 00 00 00`
- 45° → `00 00 34 42`
- 90° → `00 00 B4 42`

---

# 7. Stroke（多重ストローク）完全仕様

ストロークは次のように TLV 階層で構成される：

```
Tag 0x0201（StrokeBlock）
 └ Tag 0x0202（StrokeLayer1）
      ├ Width (float32)
      ├ Position (uint8)
      ├ Fill (solid/gradient)
 └ Tag 0x0202（StrokeLayer2）
 ...
```

### 7.1 Width（幅）float32対応
レガシーの「文字サイズに比例して拡大する」仕様と異なり  
EG は absolute 値で保持する。

---

# 8. Shadow（影）構造の詳細

```
Tag 0x0301
 ├ Distance(float32)
 ├ Angle(float32)
 ├ Blur(float32)
 ├ Opacity(uint8)
 └ Color(RGB)
```

EG は影を **1つしか保持できない**。

複数影 → 最強の影1つに圧縮する必要あり。

---

# 9. フォント構造
```
Tag 0x0401 
 ├ FontName (UTF-16LE)
 ├ FontSize (float32)
 ├ LineSpacing (float32)
 ├ Tracking (float32)
 ├ FauxBold / FauxItalic (bool)
```

---

# 10. Premiere 内部の整合性領域
バイナリの終端には以下がある：

```
00 00 00 00 01 00 00 00
```

これは AE 内部の Integrity Block（整合性チェック）  
値を変更しても再計算されるため気にしなくてよい。

---

# 11. EG で塗りの不透明度が使えない理由
EG の内部構造では：

- FillColor は RGB + Alpha を保持するが  
- Alpha は常に 255 で固定し UI から変更不可  
- XML 側の ParameterID=8（不透明度）は“Transform全体”の透明度であり塗りとは別物

→ **レガシータイトルの塗り不透明度は移植不可能、常に破棄する。**

---

# 12. レガシーから EG 変換の損失一覧（改訂版）

| 機能 | 移行可否 | 理由 |
|------|---------|------|
| グロス（Gloss） | ×（疑似3色グラデで代替） | 本体構造がEGに存在しない |
| 透明塗り | × | EGに塗り不透明度が存在しない |
| 複数影 | △（1影に圧縮） | EGは1影のみ |
| ベベル | × | EG非対応 |
| テクスチャ塗り | × | EG非対応 |
| 変形（Shear・Perspective） | × | AEテキストでは保持されない |

---

# 13. 今後の解析（v3.0 予定）
- Stroke Fill の GradientStop 48 bytes の追加領域解読  
- Shadow ブロックの 追加タグ判明  
- FontStyle（Bold/Italic/Subscript）TLV の確実化  
- Integrity Block の CRC 構造解読（必要なら）  

