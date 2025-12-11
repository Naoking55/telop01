# レガシータイトル完全移植仕様書 Part1〜3 統合版  
（PRTL / PRSL / prtextstyle / 変換アルゴリズム）

---

## 構成

- Part1: PRTL / PRSL の仕様（レガシータイトル側）
- Part2: prtextstyle の仕様（Essential Graphics テキストスタイル）
- Part3: PRTL → prtextstyle 変換アルゴリズム設計書

---

# Part1: PRTL / PRSL の仕様

## 1-1. PRTL 全体構造（テキストタイトル）

### 1-1-1. 論理構造

レガシータイトル（PRTL）は、XML 形式で以下のような要素を持つ：

- `TextDescription`  
  - フォント、文字サイズ（txHeight）、トラッキング（txKern）、行送り（leading）など
- `Style`  
  - Edge / Extrude / Fill / Shadow などの「Fragment」の集合
- `TextLine` / `TextObject`  
  - テキスト内容、配置座標、参照する Style / TextDescription への参照

大雑把なイメージ：

```xml
<PremiereData>
  <TextDescriptions>
    <TextDescription Reference="1">
      <TypeSpec txHeight="100" txKern="0" leading="100" fifullName="VD-LogoG-Extra-G" />
    </TextDescription>
    ...
  </TextDescriptions>

  <Styles>
    <Style ID="10">
      <FragmentList>
        <Fragment annotation="65538" .../>  <!-- Fill -->
        <Fragment annotation="1" .../>      <!-- Stroke1 Edge -->
        <Fragment annotation="2" .../>      <!-- Stroke2 Edge/Extrude -->
        ...
      </FragmentList>
    </Style>
  </Styles>

  <TextObjects>
    <TextObject StyleRef="10" TextRef="1" XPos="0" YPos="0">
      <TRString>テキスト</TRString>
    </TextObject>
  </TextObjects>
</PremiereData>
```

### 1-1-2. TextDescription（文字属性）

主な項目：

| 項目名        | 例           | 説明                                         |
|--------------|--------------|----------------------------------------------|
| `txHeight`   | `100`        | フォントサイズの「内部単位（unit）」         |
| `txKern`     | `0`          | トラッキング（文字間隔） unit               |
| `leading`    | `100`        | 行送り unit                                 |
| `fifullName` | `VD-LogoG-Extra-G` | フォントフルネーム（PostScript 名等） |

**重要ポイント**：

- `txHeight` / `txKern` / `leading` は、**Canvas 実装でも「unit値」として保持**する。
- 実際の px への変換は「キャンバス解像度・スケーリング」に依存させ、PRTL そのものは unit をそのまま出力・保存する方針。  

---

## 1-2. PRTL の Stroke モデル（Fragment）

### 1-2-1. Fragment の種類と annotation

- `Fragment` は主に以下の種類がある：

| annotation  | 意味              | 備考                           |
|-------------|-------------------|--------------------------------|
| `65538`     | Fill（塗り）      | 基本塗り                        |
| `65537`     | Shadow（影）      | 一般に 1 つ想定（実際は複数可） |
| `1..n`      | Stroke (Edge/Extrude) | エッジ／押し出しストローク |

実装指針：

- `annotation = 65538/65537` は「塗り / 影」として扱い、telop editor では stroke リストから除外して別管理。  

### 1-2-2. Stroke（Edge / Extrude）のデータ項目

1つの Stroke に相当する Fragment の代表的なフィールド：

| 項目名            | 型     | 例        | 説明                                        |
|------------------|--------|-----------|---------------------------------------------|
| `eFragmentType`  | enum   | `2` or `5` | 2 = Edge（輪郭） / 5 = Extrude（押し出し） |
| `size`           | int    | `100`     | Stroke 幅の内部単位（**PRTL size**）       |
| `offset`         | int    | `0` or `40` | Extrude の押し出し量など                   |
| `angle`          | float  | `0.0`     | Extrude の方向角度                          |
| `shaderRef`      | id     | `2`       | 色やグラデーションを定義する Shader 参照  |
| `placeHolder`    | bool   | `false`   | ダミー Fragment                              |

### 1-2-3. Edge / Extrude の解釈

- **Edge**
  - 元の文字アウトラインを外側に膨張させた輪郭。
  - 複数 Edge がある場合、**内側から順に外側へ累積膨張**する（PRTL 内部でも Canvas 実装でも同じ方針）。
- **Extrude**
  - 3D 的な押し出し量（Volume）を持つ。
  - Stroke の順で前後関係が決まる。  

推奨解釈：

- Stroke1 = Edge（ベース輪郭）
- Stroke2 = Extrude（Stroke1 の外側に広がる影のようなボリューム）
- Stroke3 = Edge（文字＋Extrude を含むシルエットの外側にもう一段輪郭）  

---

## 1-3. Stroke 幅「size」のスケーリングモデル（UI値との関係）

### 1-3-1. 実験から判明した事実

**重大な結論**：

1. Fragment.size 値は、**フォントサイズに完全に独立**している。  
2. UI 上の表示値（ユーザー入力値）と PRTL の `size` は**非線形な対応**を持つ。  

### 1-3-2. 実測対応表

実験で得られた「UI値 → PRTL size」の代表ペア：

| UI値 | PRTL size | 備考                    |
|------|-----------|-------------------------|
| 10   | 40        | 係数 4.0                |
| 30   | 120       | 係数 4.0                |
| 40   | 100       | 係数 2.5                |
| 80   | 250       | 係数 3.125              |
| 100  | 100       | 係数 1.0（正常サンプル）|
| 150  | 250       | 係数 1.667（正常）     |

- これより、**UI 値 10〜150 に対して単純な線形関係ではない**ことがわかる。

### 1-3-3. 変換関数（暫定仕様）

UI値 → PRTL size（エクスポート時）：

```javascript
const UI_TO_PRTL_TABLE = [
    { ui: 10,  prtl: 40 },
    { ui: 30,  prtl: 120 },
    { ui: 40,  prtl: 100 },
    { ui: 80,  prtl: 250 },
    { ui: 100, prtl: 100 },
    { ui: 150, prtl: 250 }
];

function convertUIToPRTL(uiWidth) {
    // 完全一致
    const exact = UI_TO_PRTL_TABLE.find(e => e.ui === uiWidth);
    if (exact) return exact.prtl;

    // 区間内は線形補間
    for (let i = 0; i < UI_TO_PRTL_TABLE.length - 1; i++) {
        const p1 = UI_TO_PRTL_TABLE[i];
        const p2 = UI_TO_PRTL_TABLE[i + 1];

        if (uiWidth >= p1.ui && uiWidth <= p2.ui) {
            const t = (uiWidth - p1.ui) / (p2.ui - p1.ui);
            return Math.round(p1.prtl + t * (p2.prtl - p1.prtl));
        }
    }

    // 範囲外は外挿（10未満 / 150超）
    if (uiWidth < UI_TO_PRTL_TABLE[0].ui) {
        // 10 未満: 係数 4.0 を仮定
        return Math.round(uiWidth * 4.0);
    } else {
        // 150 超: 係数 1.667 を仮定
        return Math.round(uiWidth * 1.667);
    }
}
```

PRTL size → UI値（インポート時）：

```javascript
function convertPRTLToUI(prtlSize) {
    const reverseTable = [
        { prtl: 40,  ui: 10 },
        { prtl: 100, ui: 40 },   // 100: UI=40 or 100
        { prtl: 100, ui: 100 },
        { prtl: 120, ui: 30 },
        { prtl: 250, ui: 80 },   // 250: UI=80 or 150
        { prtl: 250, ui: 150 }
    ];

    // 一致するもののうち「UI値が大きい方」を優先
    const matches = reverseTable
        .filter(e => e.prtl === prtlSize)
        .sort((a, b) => b.ui - a.ui);

    if (matches.length > 0) {
        return matches[0].ui;   // 最大 UI を採用
    }

    // 見つからなければ線形補間など（省略可）
    // ...
    return prtlSize; // 最悪 fallback（一旦同値）
}
```

---

## 1-4. PRSL（テキストスタイル）仕様

※ここでは「レガシータイトルのスタイルプリセット」を表す PRSL（最終的に 10styles.prsl など）について。

### 1-4-1. 構造概要

- PRSL は XML で、
  - 複数の `StyleProjectItem` を持つ「プロジェクト」のような構造。
  - 各 `StyleProjectItem` は 1 つのテキストスタイルプリセットを表す。
  - 内部の `Component` は `VideoFilterComponent` で、`MatchName` が `AE.ADBE Text`（After Effects テキスト）になっている。  

サンプル：

```xml
<StyleProjectItem ObjectUID="..." ClassID="..." Version="1">
  <ProjectItem Version="1">
    <Name>白・ストローク無し</Name>
  </ProjectItem>
  <Component ObjectRef="27"/>
</StyleProjectItem>

<VideoFilterComponent ObjectID="27" ClassID="..." Version="9">
  <Component Version="6">
    <Params Version="1">
      <Param Index="0" ObjectRef="40"/> <!-- ソーステキスト（バイナリ） -->
      <Param Index="1" ObjectRef="41"/> <!-- トランスフォーム -->
      ...
    </Params>
    <DisplayName>テキスト</DisplayName>
  </Component>
  <MatchName>AE.ADBE Text</MatchName>
</VideoFilterComponent>
```

### 1-4-2. Param の役割

代表的な Param：

| Index | ObjectID | Class              | ParameterID | Name             | 機能                                   |
|-------|----------|--------------------|------------|------------------|----------------------------------------|
| 0     | 40       | ArbVideo...        | 1          | ソーステキスト   | AE テキストエンジンのバイナリ blob     |
| 1     | 41       | VideoComponent...  | 2          | トランスフォーム | 位置・スケール等（使わない方針）       |
| 2     | 42       | PointComponent...  | 3          | 位置             | テキストレイヤの位置                   |
| 3     | 43       | VideoComponent...  | 4          | スケール         | 全体スケール                           |
| 7     | 47       | VideoComponent...  | 8          | 不透明度         | レイヤ全体の不透明度（テキスト＋塗り） |
| 19    | 59       | VideoComponent...  | 20         | 親の高さ         | 親コンポジション情報等                 |
| 20    | 60       | VideoComponent...  | 21         | 親の回転         | 同上                                   |

**最重要は Index=0 の `ソーステキスト`：**

```xml
<ArbVideoComponentParam ObjectID="40" ...>
  <ParameterID>1</ParameterID>
  <Name>ソーステキスト</Name>
  <StartKeyframePosition>-91445760000000000</StartKeyframePosition>
  <StartKeyframeValue Encoding="base64">
    vAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AMAAQAAwAAAA...
  </StartKeyframeValue>
</ArbVideoComponentParam>
```

- `StartKeyframeValue` は AE テキストレイヤのバイナリ構造（prtextstyle と非常に近い）。
- この blob の中に
  - フォント
  - サイズ
  - 塗り色
  - グラデーション
  - ストローク
  - シャドウ
  等が詰め込まれている。

この Part1 では「PRSL → 中間モデル」を設計し、Part2 で prtextstyle のバイナリ構造を詳述する。

---

# Part2: prtextstyle の仕様（Essential Graphics テキストスタイル）

ここでは `*.prtextstyle` 単体ファイルの仕様（XML + バイナリ）をまとめる。

## 2-1. 全体構造

`.prtextstyle` は `PremiereData` XML の中に **1 スタイル分の VideoFilterComponent** を持つ形で保存される。

典型例：

```xml
<PremiereData Version="3">
  ...
  <StyleProjectItem ObjectUID="..." ...>
    <ProjectItem ...>
      <Name>青白グラ99％</Name>
    </ProjectItem>
    <Component ObjectRef="27"/>
  </StyleProjectItem>

  <VideoFilterComponent ObjectID="27" ClassID="..." Version="9">
    <Component Version="6">
      <Params Version="1">
        <Param Index="0" ObjectRef="40"/> <!-- ソーステキスト (AE テキスト blob) -->
        <Param Index="1" ObjectRef="41"/> <!-- Transform -->
        ...
        <Param Index="21" ObjectRef="61"/> <!-- 親のフラグ -->
      </Params>
      <DisplayName>テキスト</DisplayName>
    </Component>
    <MatchName>AE.ADBE Text</MatchName>
    <VideoFilterType>2</VideoFilterType>
  </VideoFilterComponent>
  ...
</PremiereData>
```

**重要：**  
- 実際のスタイル情報は、`Param Index=0` の `ArbVideoComponentParam` にある base64 バイナリ（AE テキストスタイル blob）に格納。
- 他の Param（変形・位置・不透明度など）は原則無視し、**telop editor 側では独自 UI と Canvas で管理**する。

---

## 2-2. AE テキストスタイル blob（base64）のバイナリ概要

### 2-2-1. 先頭 0x00〜0x20 のヘッダ

Hex 例（単色 Fill + 黒 Stroke テンプレート）  

```text
00000000: bc 01 00 00 00 00 00 00 44 33 22 11 0c 00 00 00
00000010: 00 00 06 00 0a 00 04 00 06 00 00 00 64 00 00 00
00000020: 00 00 5e 00 30 00 10 00 0c 00 00 00 ...
```

- ここには
  - 総バイト長
  - 固定マジック `44 33 22 11`
  - 각セクションへのオフセット（`0x5e`, `0x30`, ...）
  が入っている。
- オフセット値は小さい順で並び、TLV（Tag-Length-Value）ブロックの開始位置を指す。

### 2-2-2. Gradient / Fill 情報ブロック

Hex 例（多色グラデーション）から抽出された Stop 構造：  

```text
Stop0 開始位置: 0x0275
00000275: 00 09 00 0a 00 00 00 00 00 00 ff ff ff 0a 00 08 ...
```

- 実験からの結論：
  - **1 Stop あたり 48 bytes**（= 0x30）で構造が繰り返される。  
  - 含まれる情報：
    - Stop インデックス
    - Location（0.0〜1.0 float32）
    - Midpoint（0.0〜1.0 float32）
    - 色（RGBA 4 bytes, 多くの場合 `FF FF FF FC` など先頭 3byte=RGB, 末尾=Alpha もしくはフラグ）
- Stop の個数は、別の「Count」フィールドで管理されており、Stops を増減すると
  - バイナリサイズ
  - Count 値
  - 後続ブロックのオフセット
  が変化する。

#### 位置と中間点の UI 対応

- Premiere UI 上の「位置」スライダ: 0〜100%
- 「中間点」スライダ 0〜100%

AE テキスト blob 内では：

- Location = UI位置 / 100.0 （float32）
- Midpoint = UI中間点 / 100.0 （float32）

という線形対応が確認できる（2色・3色・4色グラでの差分から）。

---

## 2-3. Stroke / Shadow 情報ブロック（概要）

Stroke も Gradient と同様に TLV ブロックとして存在する。

仮モデル：

```ts
type StrokeBlock = {
  enabled: boolean;
  kind: 'edge' | 'shadow';
  width: number;          // UI값（px 相当）
  color: RGBA;            // 4 bytes
  opacity: number;        // 0..100
  join: 'round' | 'miter' | 'bevel';
  position: 'outside' | 'center' | 'inside';   // 実際は AE 中で別の表現
  blur: number;           // shadow の場合
  angle: number;          // shadow の場合
  distance: number;       // shadow の場合
};
```

実際の Hex（TEMPLATE_* 系）から得られた知見：

- Stroke ブロックは、
  - 幅
  - 色
  - 透明度
  - オン/オフ
 を含む 1 セットとして繰り返されている。
- Stroke を OFF にすると
  - `enabled` フラグ
  - opacity=0
  の組み合わせで表現される（完全な 0 化）。

---

## 2-4. PRTL 機能との対応表（何が移せるか）

Part2 のまとめとして、「レガシータイトル機能 → EG / prtextstyle での対応」を整理：

| レガシー機能            | EG / prtextstyle での対応     | 備考                            |
|-------------------------|-------------------------------|---------------------------------|
| 単色塗り（Fill）       | ○ 完全対応                    | RGB 一致                        |
| 2色グラデーション       | ○ 完全対応                    | Angle / Location / Midpoint 済 |
| 3色以上グラデーション   | ○ 完全対応                    | Stop 数上限ほぼなし            |
| 光沢（Gloss）           | △ 3色グラデーションへ近似     | 中央を明るくした疑似反射        |
| 多重ストローク          | ○ 完全対応（EG は無制限）     | Stroke 数の論理上限なし        |
| 複数シャドウ            | △ 1 個のドロップシャドウに圧縮 | 代表値 1 つに集約               |
| 塗りの不透明度          | × 捨てる                       | EG のテキスト塗りは 100% 固定  |
| ベベル / エンボス       | × 完全に破棄                  | EG 側に同等機能なし             |
| 文字属性（フォント等）  | ○ 完全対応                    | フォント・サイズ・行送り等     |

**決定事項：**

- **塗りの不透明度（Fill Opacity）は完全に無視して変換**する。
  - すべて 100% 不透明として扱う（ユーザーも「EG ではできなくなった」ことを確認済み）。
- ベベル・エンボス等は **変換段階で破棄** し、将来的に Canvas 側の独自機能として再設計する。

---

# Part3: PRTL → prtextstyle 変換アルゴリズム設計書

ここでは「レガシータイトル（PRTL/PRSL）から EG テキストスタイル（prtextstyle）への変換」を**完全なパイプラインとして設計**する。

## 3-1. 全体フロー

1. PRSL / PRTL を読み込み、**中間モデル（LegacyStyle）** に落とし込む
2. 中間モデルを **EGスタイルモデル（EgTextStyle）** にマッピング
3. `EgTextStyle` を AE テキストバイナリ blob（prtextstyle base64）としてシリアライズ
4. `.prtextstyle` XML として書き出す

---

## 3-2. 中間モデル定義

### 3-2-1. LegacyStroke

```ts
type LegacyStrokeKind = 'edge' | 'extrude' | 'shadow';

interface LegacyStroke {
  kind: LegacyStrokeKind;
  uiWidth: number;         // レガシー UI 表示値（px 相当）
  prtlSize: number;        // PRTL Fragment.size (unit)
  color: { r: number; g: number; b: number; };
  opacity: number;         // 0..100
  angle: number;           // deg
  distance: number;        // shadow 等
  blur: number;            // shadow 等
  order: number;           // 内側からの順序
}
```

### 3-2-2. LegacyFill / LegacyGradientStop

```ts
interface LegacyFillSolid {
  type: 'solid';
  color: { r: number; g: number; b: number; };
  // 塗り不透明度は EG 非対応のため保持しない／使わない
}

interface LegacyGradientStop {
  position: number;   // 0.0〜1.0
  midpoint: number;   // 0.0〜1.0
  color: { r: number; g: number; b: number; };
}

interface LegacyFillGradient {
  type: 'gradient';
  angle: number;
  stops: LegacyGradientStop[];
}

type LegacyFill = LegacyFillSolid | LegacyFillGradient;
```

### 3-2-3. LegacyTextStyle

```ts
interface LegacyTextStyle {
  name: string;
  fontFamily: string;
  fontStyle: string;       // Regular / Bold 等（取れる範囲で）
  fontSizeUnit: number;    // txHeight
  trackingUnit: number;    // txKern
  leadingUnit: number;     // leading

  fill: LegacyFill;
  strokes: LegacyStroke[]; // kind=edge/extrude/shadow
}
```

---

## 3-3. EG Text Style モデル

```ts
type EgFill =
  | { type: 'none' }
  | { type: 'solid'; color: { r:number; g:number; b:number; }; }
  | { type: 'gradient'; angle:number; stops: EgGradientStop[]; };

interface EgGradientStop {
  position: number;  // 0.0〜1.0
  midpoint: number;  // 0.0〜1.0
  color: { r:number; g:number; b:number; };
}

interface EgStroke {
  enabled: boolean;
  kind: 'edge';     // EG では全て edge として扱う（extrude を含めて擬似的に）
  width: number;    // UI px 値
  color: { r:number; g:number; b:number; };
  opacity: number;  // 0..100
  order: number;
}

interface EgShadow {
  enabled: boolean;
  color: { r:number; g:number; b:number; };
  opacity: number;
  angle: number;
  distance: number;
  blur: number;
}

interface EgTextStyle {
  name: string;
  fontFamily: string;
  fontStyle: string;
  fontSizePx: number;
  tracking: number;
  leading: number;

  fill: EgFill;
  strokes: EgStroke[];
  shadow: EgShadow | null;
}
```

---

## 3-4. 変換ステップ詳細

### 3-4-1. ステップA：PRSL / PRTL → LegacyTextStyle

#### PRSL の場合

1. `StyleProjectItem` を列挙
2. 各 `Component.MatchName == "AE.ADBE Text"` を対象
3. `Param Index=0` の `StartKeyframeValue`（base64）をデコード
4. 既存解析済みの Hex テンプレートに基づき
   - フォント／サイズ／トラッキング／行送り
   - Fill（単色 or グラデーション）
   - Stroke / Shadow
   を抽出し、`LegacyTextStyle` にマッピング

#### PRTL の場合

1. XML `TextDescriptions` から文字属性を抽出
2. `Styles / FragmentList` から Stroke / Fill / Shadow を抽出
3. Fragment.size を `convertPRTLToUI` で UI値に変換し `uiWidth` として保存
4. Gradient Shader から Stop/Color/Angle を抽出し `LegacyFillGradient` を構築

---

### 3-4-2. ステップB：LegacyTextStyle → EgTextStyle

```ts
function convertLegacyToEg(legacy: LegacyTextStyle): EgTextStyle {
  // 1. フォント系
  const fontSizePx = legacy.fontSizeUnit; // ここは 1:1 で扱う（Canvas 側で最終調整）

  // 2. Fill
  let fill: EgFill;
  if (legacy.fill.type === 'solid') {
    fill = {
      type: 'solid',
      color: legacy.fill.color
      // 塗り不透明度は EG 非対応なので 100% 固定
    };
  } else {
    fill = {
      type: 'gradient',
      angle: legacy.fill.angle,
      stops: legacy.fill.stops.map(s => ({
        position: s.position,
        midpoint: s.midpoint,
        color: s.color
      }))
    };
  }

  // 3. Stroke（Edge + Extrude を Edge に正規化）
  const edgeStrokes = legacy.strokes
    .filter(s => s.kind === 'edge' || s.kind === 'extrude')
    .map((s, index) => ({
      enabled: true,
      kind: 'edge',
      width: s.uiWidth,  // UI値をそのまま EG に渡す
      color: s.color,
      opacity: s.opacity,
      order: index
    }));

  // 4. Shadow（複数があっても代表1つに集約）
  const shadows = legacy.strokes.filter(s => s.kind === 'shadow');
  let shadow: EgShadow | null = null;
  if (shadows.length > 0) {
    const s = shadows[0]; // もっとも外側 or 最初のものを採用（ポリシー次第）
    shadow = {
      enabled: true,
      color: s.color,
      opacity: s.opacity,
      angle: s.angle,
      distance: s.distance,
      blur: s.blur
    };
  }

  return {
    name: legacy.name,
    fontFamily: legacy.fontFamily,
    fontStyle: legacy.fontStyle,
    fontSizePx,
    tracking: legacy.trackingUnit,
    leading: legacy.leadingUnit,
    fill,
    strokes: edgeStrokes,
    shadow
  };
}
```

**この段階での“捨てる情報”：**

- 塗りの不透明度（Fill opacity）  
  → EG ではサポートされないため **常に 100%** に正規化。
- ベベル / エンボスなどの 3D 効果  
  → EG にないため **完全削除**。
- 複数シャドウ → 1 個に圧縮  
  → 見た目にもっとも支配的なものを採用（距離・濃さが大きい方など）。

---

### 3-4-3. ステップC：EgTextStyle → prtextstyle バイナリ

1. AE テキストスタイル blob の初期テンプレート（Base）を用意する
   - 単色白塗り + Stroke なし + Shadow なし のデフォルト
2. `EgTextStyle` の内容に応じて blob 内の TLV ブロックを書き換える：
   - フォント名／サイズ／トラッキング／行送り
   - Fill:
     - 単色 → 単色 Fill ブロックの RGB を書き換え
     - グラデ → Stop 数を変更し、各 Stop の位置 / 中間点 / 色を書き換え
   - Stroke:
     - Stroke 数分の Stroke ブロックを生成し、幅・色・opacity をセット
   - Shadow:
     - Shadow ブロックを生成/更新し、angle / distance / blur / color / opacity をセット
3. blob 全体長、各オフセット、Stop 数などを再計算してヘッダを書き換え

最後に：

- blob を base64 エンコード
- それを `ArbVideoComponentParam.StartKeyframeValue` に埋め込む
- 周辺 XML（StyleProjectItem / VideoFilterComponent）を組み立てて `.prtextstyle` として書き出す。

---

## 3-5. 損失と互換性ポリシーまとめ

1. **完全に保持されるもの**
   - フォント／サイズ／行送り／トラッキング
   - 単色塗り（RGB）
   - 2色以上のグラデーション（Stop 位置 / 中間点 / 色）
   - ストローク数・色・太さ（UI値として）
2. **縮退して保持されるもの**
   - 複数シャドウ → 1 つのドロップシャドウに集約
   - Edge / Extrude の区別 → すべて Edge としてモデリング（見た目を合わせる）
3. **破棄されるもの**
   - 塗りの不透明度（Fill opacity）
   - ベベル / エンボス（3D 効果）
   - EG で再現不能な一部のブレンドモード・ハイライト効果

---

以上が「Part1: PRTL/PRSL」「Part2: prtextstyle」「Part3: 変換アルゴリズム」を統合した仕様書です。  
このまま Part4〜9 の後編と組み合わせれば、レガシータイトル完全移植系の「上巻＋下巻」になる想定です。
