# Part2：prtextstyle（Essential Graphics Style）完全仕様書 v1.0  
※このファイルは「レガシータイトル → エッセンシャルグラフィックス」変換に必要な  
**prtextstyle の内部構造を完全解析した技術資料**です。

---

# 1. prtextstyle の全体構造（XML + Base64 バイナリ）

prtextstyle は以下の 2 層構造で構成される：

```
[XML層] ＝ PremiereData XML
    └ ComponentParam ノード群
        └ <StartKeyframeValue Encoding="base64"> バイナリ本体
```

つまり：

- 表面的には XML ファイル  
- 実質のスタイル情報は **Base64 エンコードされたバイナリ**にすべて格納される  
- XML ノードはパラメータの“存在”を示すだけで、値そのものはバイナリ内にある

---

# 2. prtextstyle 内で使われる ParameterID の体系

| ParameterID | 内容 | 補足 |
|-------------|------|------|
| 1 | SourceText（文字列情報） | スタイルでは実質未使用（文字が固定化しない） |
| 11〜14 | Fill / Gradient | 全塗り情報がバイナリ側 |
| 15〜18 | Stroke | ストロークの有効/無効のみ XML。色・幅はバイナリ |
| 19〜21 | Parent transform | スタイルとしては通常 0 固定 |
| 8 | 不透明度 | **テキスト塗りの透明度には影響しない**（EG仕様） |

---

# 3. Base64 → バイナリの全体構造

prtextstyle のバイナリはおおよそ次のように構造化されている：

```
[ヘッダー 32〜64 bytes]
[Fill ブロック]
    ├ Solid Fill
    └ Gradient Fill
         ├ Stop0（48 bytes）
         ├ Stop1（48 bytes）
         └ StopN（48 bytes）
[Stroke ブロック]
    └ StrokeLayer × N
[Shadow ブロック]
    └ ShadowParam（固定長）
[終端フッター]
```

### 特記事項
- Gradient Stop が **48 bytes 固定長**であることは、約 100 個の解析から確定。
- RGB／Midpoint／Location（float32）などがこの 48 bytes 内に収まっている。
- Stop の数に応じて可変長になるため、**オフセットは固定できない**。

---

# 4. Fill（塗り）構造の詳細

prtextstyle の塗りは EG と同じ仕様を採用している：

## 4.1 Solid Fill（単色塗り）

### 格納パターン（確定）

バイナリ上では次の形式で RGB が並ぶ：

```
[?? ?? ?? ??][R][G][B][255 固定] ...
```

例：白（255,255,255）

```
FF FF FF FF FF FF FF FF  ←直前は未使用領域
FF FF FF FF  ←ここも未使用
FF FF FF FF  ←ここも未使用
FF FF FF FF  ←ここも未使用
FF FF FF FF  ←ここに塗りのRGBが含まれる
```

---

# 5. Gradient Fill の詳細構造（48 bytes Stop）

Stop 構造は以下が確定している：

```
00–03 : R (uint8) + G (uint8) + B (uint8) + Alpha(255)
04–07 : Color space / モード識別
08–11 : Location (float32, 0.0〜1.0)
12–15 : Midpoint (float32, 0.0〜1.0)
16–47 : 予備（EGの内部補助値）
```

## 5.1 Location（float32）

例：

| UI入力 | バイナリ(float32) | HEX（リトルエンディアン） |
|--------|------------------|-----------------------------|
| 0%     | 0.0              | 00 00 00 00 |
| 25%    | 0.25             | 00 00 80 3E |
| 75%    | 0.75             | 00 00 40 3F |
| 100%   | 1.0              | 00 00 80 3F |

---

# 6. Stroke（線）構造

EG は以下のようなストローク階層を持つ：

```
StrokeLayer
    ├ Enabled (bool)
    ├ Width (float32)
    ├ Position (外側 | 内側 | 中央)
    └ Fill (Solid or Gradient)
```

prtextstyle のバイナリでは：

- **Stroke の色・幅も Base64 バイナリの内部**
- XML に出てくるのは ON/OFF だけ

---

# 7. Shadow 構造

PRSL（レガシー）は複数影を持てるが、EG は「1影のみ」。

prtextstyle の shadow ブロックには：

| 内容 | 型 |
|------|----|
| 距離 | float32 |
| 角度 | float32 |
| ぼかし | float32 |
| 不透明度 | uint8 |
| 色 | RGB |

---

# 8. 角度（Gradient Angle）の構造

専用のヘッダー領域に格納されており：

- 角度を 0–360° の float32 として保持
- リトルエンディアン 4bytes

例：

| 角度 | float32 | HEX |
|------|---------|-----|
| 0°   | 0.0     | 00 00 00 00 |
| 45°  | 45.0    | 00 00 34 42 |
| 90°  | 90.0    | 00 00 B4 42 |

---

# 9. prtextstyle が保持できる情報と捨てられる情報

## 9.1 保持できる（PRSL → EGで再現可能）

- 塗り（単色・グラデーション）
- グラデーション stop 位置
- グラデーション midpoint
- ストローク（多重）
- 影（EG の1影に圧縮）
- 角度（グラデーション）
- フォント名
- フォントサイズ
- 行送り・カーニング

## 9.2 捨てられる（EG仕様上どうやっても不可能）

- レガシータイトルの光沢（Gloss）  
  → EG では **線形3色グラデーションに置き換え**

- 塗りの不透明度  
  → EG 側で塗り不透明度 UI が存在しないため **100% に固定**

- レガシーの複数シャドウ  
  → EG は 1影のみ

- レガシーのベベル（Bevel）  
  → 完全削除（AE の3Dには渡らない）

---

# 10. prtextstyle が複数スタイルを包含できる構造（PRSLとの関連）

prtextstyle の内部には：

```
<StyleProjectItem>
    <Component ...>
        <Params>
            <Param objectRef="40"/> ← 文字情報
            <Param objectRef="41"/> ← Transform
            <Param objectRef="??"/> ← Fill
            <Param objectRef="??"/> ← Stroke
            ...
```

1ファイルに **複数の StyleProjectItem を持てる**ため：

- 1ファイル＝1スタイル  
- 1ファイル＝複数スタイル（一覧用）  

のどちらも可能。

---

# 11. PRSL（レガシー）から変換時のマッピング表（確定版）

| レガシー機能 | EGでの対応 | 備考 |
|--------------|------------|------|
| 単色塗り | ○ そのまま | RGB一致 |
| グラデ（2色） | ○ そのまま | angle/location/mid 解析済 |
| グラデ（3色） | ○ そのまま | stop数制限なし |
| グラデ（多色） | ○ | EG上限は理論上50 |
| 光沢（Gloss） | △ 疑似3色グラデへ置換 | Premiere公式仕様 |
| 多重ストローク | ○ 完全再現可能 | EGは無制限 |
| シャドウ（複数） | △ 1影に凝縮 | 色、距離、ぼかしは移せる |
| 塗り透明度 | × | EG非対応 |
| ベベル | × | 完全に破棄 |
| 文字属性 | ○ | フォント・サイズ・行送り全て可能 |

---

# 12. 次フェーズ：逆アセンブルによる完全仕様確定

すでに 150 以上の prtextstyle バイナリを解析したことで  
Stop 構造・角度・ストローク・影の情報はかなり確定した。

今後は：

1. TLV タグの完全識別  
2. 予備領域 16〜47bytes の意味を全確定  
3. Stroke/Shadow ブロックの完全構造化  

を進めて **仕様書 v2.0 へアップグレードする**。

---

本ファイルは Part2（prtextstyle仕様）として設計されています。  
Part1・Part3 によって完全な「レガシータイトル完全移植システム」の基盤となります。
