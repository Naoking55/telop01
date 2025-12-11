# PRTL / PRSL（レガシータイトル）完全仕様書 v1.0（詳細版）

---

## 1. PRTL（Legacy Title）の全体構造

PRTL は Adobe Premiere Pro の旧式タイトルエンジンで、以下の二層構造で構成される：

1. **XML構造**（タイトルの一般メタ情報）
2. **バイナリ Blob（Base64）**  
   Fill / Stroke / Shadow などの詳細パラメータを保持する。

---

## 2. XML の代表構造

```xml
<PremiereData Version="3">
  <Project ... />
  <StyleProjectItem>
    <Component>
       <Params>
         <Param Index="0" ObjectRef="40"/>  ← Fill / Text
         <Param Index="1" ObjectRef="41"/>  ← Transform
         ...
       </Params>
    </Component>
  </StyleProjectItem>
</PremiereData>
```

ParamID の割り当て（Legacy）：

|ID|意味|
|---|---|
|1|テキスト内容（UTF-16 Base64）|
|3|位置|
|4|スケール|
|7|回転|
|8|不透明度（全体）|

---

## 3. Legacy のストローク仕様（完全）

### ✔ 多重ストロークに対応（最大8–10本）
- 各ストロークは外側方向に拡張
- 計算式：  
  **width_final = Σ stroke[i].width**

### ✔ ストロークの属性

|項目|内容|
|---|---|
|width|整数値（px）|
|color|RGB（uint8 ×3）|
|opacity|0–255|
|join|Legacy 内部値固定（Miter 等）|

---

## 4. Legacy グラデーション Fill の仕様

### Stop 数：最大16

Stop形式：

|項目|型|説明|
|---|---|---|
|offset|0.0〜1.0|
|color|RGB|
|alpha|不透明度|
|midpoint|Stop間補間率|

---

## 5. レガシー独自機能（EG非対応）

|機能|状態|
|---|---|
|光沢（Gloss）|EGに無い → 3色グラデに変換|
|エンボス|削除|
|多重ストローク|1本に縮約|
|テクスチャ|削除|

---

## 6. PRSL（Legacy Style Library）の仕様

PRSL は複数のスタイル（PRTL の一部）をまとめた XML ファイル。

- 内部には StyleProjectItem が複数存在
- 各アイテムが個別のタイトルスタイルを保持
- 中には Base64 パラメータをそのまま含む

**PRSL → prtextstyle 変換では以下を抽出：**

- Fill
- Stroke（多重 → 最外1本）
- Shadow
- Font 情報
- Transform（位置・回転などは破棄）
