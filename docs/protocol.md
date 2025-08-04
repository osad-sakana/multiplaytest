# 通信プロトコル仕様書

## 概要

クライアントとサーバー間の WebSocket 通信に使用される JSON メッセージプロトコルの仕様です。

## 基本仕様

- **プロトコル**: WebSocket (RFC 6455)
- **メッセージ形式**: JSON
- **エンコーディング**: UTF-8
- **エンドポイント**: `ws://localhost:8000/ws`

## メッセージ構造

すべてのメッセージは以下の基本構造を持ちます：

```json
{
  \"type\": \"message_type\",
  \"data\": {
    // メッセージ固有のデータ
  }
}
```

## クライアント → サーバー メッセージ

### 1. プレイヤー参加 (join)

```json
{
  \"type\": \"join\",
  \"name\": \"PlayerName\"
}
```

- **用途**: ゲームへの参加とプレイヤー名の登録
- **必須フィールド**: `name`
- **タイミング**: WebSocket 接続直後に送信
- **制限**: 1接続につき1回のみ

### 2. プレイヤー入力 (input)

```json
{
  \"type\": \"input\",
  \"action\": \"move\",
  \"direction\": \"up\"
}
```

#### パラメータ
- **`action`**: 
  - `\"move\"`: 通常移動
  - `\"dash\"`: ダッシュ移動
- **`direction`**: 
  - `\"up\"`: 上方向
  - `\"down\"`: 下方向  
  - `\"left\"`: 左方向
  - `\"right\"`: 右方向

#### 送信タイミング
- キー押下時に連続送信
- フレームレート: 60 FPS
- 複数方向の同時入力可能

## サーバー → クライアント メッセージ

### 1. ゲーム状態 (game_state)

```json
{
  \"type\": \"game_state\",
  \"data\": {
    \"players\": {
      \"player_id_1\": {
        \"id\": \"550e8400-e29b-41d4-a716-446655440000\",
        \"name\": \"Player1\",
        \"x\": 400.0,
        \"y\": 300.0,
        \"color\": [255, 128, 64],
        \"deaths\": 0,
        \"is_dashing\": false,
        \"dash_cooldown\": 0.0
      },
      \"player_id_2\": {
        // 他のプレイヤーデータ
      }
    },
    \"field_width\": 800,
    \"field_height\": 600,
    \"player_size\": 30,
    \"your_player_id\": \"550e8400-e29b-41d4-a716-446655440000\"
  }
}
```

- **用途**: プレイヤー参加時の初期ゲーム状態送信
- **送信タイミング**: プレイヤーの `join` メッセージ受信後
- **送信先**: 参加したプレイヤーのみ

### 2. プレイヤー更新 (player_update)

```json
{
  \"type\": \"player_update\",
  \"data\": {
    \"player\": {
      \"id\": \"550e8400-e29b-41d4-a716-446655440000\",
      \"name\": \"Player1\",
      \"x\": 405.0,
      \"y\": 300.0,
      \"color\": [255, 128, 64],
      \"deaths\": 0,
      \"is_dashing\": true,
      \"dash_cooldown\": 1634567890.5
    }
  }
}
```

- **用途**: プレイヤーの位置・状態変更の通知
- **送信タイミング**: プレイヤーの移動・ダッシュ時
- **送信先**: 全プレイヤー（ブロードキャスト）

### 3. プレイヤー参加通知 (player_joined)

```json
{
  \"type\": \"player_joined\",
  \"data\": {
    \"player\": {
      \"id\": \"550e8400-e29b-41d4-a716-446655440000\",
      \"name\": \"NewPlayer\",
      \"x\": 400.0,
      \"y\": 300.0,
      \"color\": [128, 255, 192],
      \"deaths\": 0,
      \"is_dashing\": false,
      \"dash_cooldown\": 0.0
    }
  }
}
```

- **用途**: 新しいプレイヤーの参加通知
- **送信タイミング**: プレイヤーが参加した時
- **送信先**: 全プレイヤー（ブロードキャスト）

### 4. プレイヤー離脱通知 (player_left)

```json
{
  \"type\": \"player_left\",
  \"data\": {
    \"player_id\": \"550e8400-e29b-41d4-a716-446655440000\"
  }
}
```

- **用途**: プレイヤーの離脱通知
- **送信タイミング**: WebSocket 接続切断時
- **送信先**: 残りの全プレイヤー（ブロードキャスト）

### 5. リスポーン通知 (respawn)

```json
{
  \"type\": \"respawn\",
  \"data\": {
    \"player\": {
      \"id\": \"550e8400-e29b-41d4-a716-446655440000\",
      \"name\": \"Player1\",
      \"x\": 400.0,
      \"y\": 300.0,
      \"color\": [255, 128, 64],
      \"deaths\": 1,
      \"is_dashing\": false,
      \"dash_cooldown\": 0.0
    }
  }
}
```

- **用途**: プレイヤーの場外落下とリスポーン通知
- **送信タイミング**: 場外判定時
- **送信先**: 全プレイヤー（ブロードキャスト）

## データ型仕様

### Player オブジェクト
```typescript
interface Player {
  id: string;              // UUID v4 形式
  name: string;            // プレイヤー名（最大長制限なし）
  x: number;               // X座標（浮動小数点）
  y: number;               // Y座標（浮動小数点）
  color: [number, number, number];  // RGB値 [0-255, 0-255, 0-255]
  deaths: number;          // 死亡回数（非負整数）
  is_dashing: boolean;     // ダッシュ状態
  dash_cooldown: number;   // ダッシュクールダウン時刻（UNIX timestamp）
}
```

### ゲーム定数
```typescript
interface GameConstants {
  field_width: 800;        // フィールド幅（ピクセル）
  field_height: 600;       // フィールド高さ（ピクセル）
  player_size: 30;         // プレイヤーサイズ（ピクセル）
}
```

## 通信フロー

### 1. プレイヤー参加フロー
```
Client                           Server                          Other Clients
  |                                |                                |
  |-- WebSocket Connect ---------->|                                |
  |<-- Connection Established -----|                                |
  |                                |                                |
  |-- join: {name: \"Player1\"} ---->|                                |
  |                                |-- player_joined: {player} ---->|
  |<-- game_state: {全状態} --------|                                |
  |                                |                                |
```

### 2. ゲームプレイフロー
```
Client                           Server                          Other Clients
  |                                |                                |
  |-- input: {action, direction} ->|                                |
  |                                |-- ゲームロジック実行 --|        |
  |                                |-- player_update: {player} ---->|
  |<-- player_update: {player} ----|                                |
  |                                |                                |
```

### 3. 場外判定フロー
```  
Client                           Server                          Other Clients
  |                                |                                |
  |-- input: {dash, direction} --->|                                |
  |                                |-- 場外判定 → True --|          |
  |                                |-- deaths++ --|                 |
  |                                |-- respawn: {player} ---------->|
  |<-- respawn: {player} ----------|                                |
  |                                |                                |
```

## エラーハンドリング

### 接続エラー
- **WebSocket接続失敗**: クライアント側でタイムアウト（5秒）
- **認証なし**: 現在未実装（将来的に追加予定）

### メッセージエラー
- **不正なJSON**: サーバー側で無視（ログ出力）
- **未知のメッセージタイプ**: サーバー側で無視
- **必須フィールド欠如**: Pydantic バリデーションエラー

### 通信エラー
- **接続切断**: 
  - クライアント: 自動的に接続画面に戻る
  - サーバー: プレイヤー削除とブロードキャスト
- **メッセージ送信失敗**: 接続状態を無効に設定

## パフォーマンス特性

### メッセージ頻度
- **input**: 最大 60 msg/sec（フレームレート依存）
- **player_update**: プレイヤー数 × 移動頻度
- **その他**: イベント駆動型

### メッセージサイズ
- **input**: ~50 bytes
- **player_update**: ~150 bytes
- **game_state**: プレイヤー数 × 150 bytes + 100 bytes

### レイテンシ
- **ローカル**: < 1ms
- **LAN**: < 10ms  
- **インターネット**: ネットワーク依存