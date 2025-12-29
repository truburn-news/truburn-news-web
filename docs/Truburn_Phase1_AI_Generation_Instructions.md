# Truburn Phase1 – AI生成開発指示書（Wallet Mock版）

## 目的
本ドキュメントは、Truburn Phase1（ウォレット認証をモック化したMVP）を、
**すべて生成AI（コーディングAI／エージェント）により実装させるための唯一の指示書**である。

本mdファイルのみを入力として、
- 仕様理解
- 設計
- 実装
- 最低限のUI構築
を一気通貫で行うことを目的とする。

---

## 前提思想（絶対に破ってはいけない）

- Truburnは「ニュースサイト」ではない
- 出来事は **Record（検証可能な記録）** として扱う
- 真実を断定しない
- 重要なのは **発生時刻の解像度（時間幅）**
- 未確定は悪ではないが、断定は危険

AIは「裁判官」ではなく「検証補助装置」である。

---

## Phase1の制約（重要）

- ウォレット認証は **モック実装**
- トークン・暗号資産・換金なし
- DAO / 投票 / 多数決なし
- 金銭価値を持たない内部単位のみ使用
- 検証は必ず有限期間で確定

---

## 用語定義（Phase1限定）

| 用語 | 意味 |
|---|---|
| Record | 出来事を記述した検証対象 |
| Resolution | 発生時刻の精度（時間幅） |
| VP | Verification Point（内部評価単位） |
| Review Request | VPを消費して行う検証申請 |
| VERIFIED | 検証期間内に有効な反証が無かった状態 |
| FALSIFIED | 反証により矛盾が証明された状態 |

---

## システム構成（固定）

- Backend: FastAPI (Python)
- DB: PostgreSQL
- ORM: SQLAlchemy
- Migration: Alembic
- Frontend: Jinja2 + HTMX
- Auth: Wallet風モックログイン（UUID生成）

---

## 必須ページ構成

- /auth : ログイン（モック）
- /onboarding : 初回チュートリアル
- /feed/live : 未検証Record一覧
- /feed/investigating : 検証中
- /feed/archive : 確定Record
- /report : 新規投稿
- /case/{id} : 検証ページ
- /vault : マイページ
- /about : プロジェクト説明

---

## コア機能要件

### 1. Record投稿

- タイトル
- 本文
- 発生時刻 start / end
- Resolution自動算出
- Evidence（URLのみで可）

### 2. Resolutionロジック

- 時間幅が短いほど高解像度
- 解像度は整数（1〜5）
- UIに倍率として表示（例: x1.0〜x2.5）

### 3. Review Request（検証申請）

- VPを消費
- 理由テキスト必須（200文字以上）
- 反証Evidence必須（URL）
- RecordはUNDER_REVIEWへ

### 4. 検証確定

- 検証期限（72時間）
- 期限到達時に自動確定
- 反証あり → FALSIFIED
- 反証なし → VERIFIED

---

## AIの役割制限

AIは以下のみを行う：

- 時刻記述の曖昧さ検出
- 5W1H不足の警告
- 因果関係の形式チェック

以下は禁止：

- 真偽の断定
- 正誤判定
- 結論の提示

---

## 実装指示（生成AI向け）

あなたは以下を **順番通り** 実装してください。

1. プロジェクト構成作成
2. DBスキーマ定義
3. Alembic初期Migration
4. FastAPIルータ実装
5. HTMX対応テンプレ作成
6. Review確定バッチ
7. 最低限のCSS

コードはすべて動作する形で出力すること。

---

## 成功条件

- ローカルで起動できる
- 投稿 → 検証申請 → 確定まで一連で動く
- ウォレットは不要
- 金銭・トークン要素なし

---

## 最終メッセージ

Truburn Phase1は、
「真実を決めるシステム」ではない。

**検証できる形で、曖昧さを減らすための装置**である。

その思想を、コード・UI・仕様のすべてに反映せよ。
