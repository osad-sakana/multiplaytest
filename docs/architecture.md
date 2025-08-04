# アーキテクチャ概要

## システム概要

マルチプレイゲームは、以下のコンポーネントで構成されるクライアント・サーバーアーキテクチャを採用しています：

- **サーバー**: FastAPI + WebSocket によるゲーム状態管理とリアルタイム通信
- **クライアント**: Pygame による描画と入力処理
- **通信**: WebSocket を使ったリアルタイム双方向通信

## アーキテクチャ図

```
┌─────────────────┐    WebSocket     ┌─────────────────┐
│                 │ ←──────────────→ │                 │
│  Pygame Client  │                  │  FastAPI Server │
│                 │  JSON Messages   │                 │
│ ┌─────────────┐ │                  │ ┌─────────────┐ │
│ │ Game Loop   │ │                  │ │ GameManager │ │
│ │ Input       │ │                  │ │ WebSocket   │ │
│ │ Rendering   │ │                  │ │ Handler     │ │
│ └─────────────┘ │                  │ └─────────────┘ │
└─────────────────┘                  └─────────────────┘
        │                                      │
        │                                      │
   ┌─────────┐                           ┌──────────┐
   │ Player  │                           │ Docker   │
   │ Input   │                           │ Container│
   └─────────┘                           └──────────┘
```

## 主要コンポーネント

### サーバーサイド (`server/`)

#### 1. FastAPI アプリケーション (`main.py`)
- WebSocket エンドポイント `/ws` の提供
- RESTful API エンドポイント（ヘルスチェック等）
- CORS 設定とミドルウェア管理

#### 2. ゲームマネージャー (`game_state.py`)
- プレイヤー状態の管理（位置、色、スコア）
- ゲームロジックの実行（移動、ダッシュ、場外判定）
- WebSocket クライアントへのブロードキャスト

#### 3. データモデル (`models.py`)
- Pydantic を使用したデータ検証
- `Player`, `GameState`, `PlayerInput`, `GameUpdate` モデル

### クライアントサイド (`client/`)

#### 1. メインゲームループ (`main.py`)
- Pygame イベント処理
- 接続状態管理
- 画面遷移制御（接続画面 ↔ ゲーム画面）

#### 2. WebSocket通信 (`game_client.py`)
- 非同期WebSocket通信の管理
- メッセージハンドラーの登録・実行
- 接続状態の監視

#### 3. 描画エンジン (`renderer.py`)
- Pygame を使った2D描画
- UI要素の表示（スコアボード、操作説明）
- アニメーション効果（ダッシュエフェクト等）

## データフロー

### 1. プレイヤー参加フロー
```
Client → Server: {"type": "join", "name": "PlayerName"}
Server → All Clients: {"type": "player_joined", "data": {player_data}}
Server → New Client: {"type": "game_state", "data": {全ゲーム状態}}
```

### 2. 入力処理フロー
```
Client Input → Client: キー入力検出
Client → Server: {"type": "input", "action": "move|dash", "direction": "up|down|left|right"}
Server: ゲームロジック実行（位置更新、衝突判定）
Server → All Clients: {"type": "player_update", "data": {updated_player}}
```

### 3. 場外判定フロー
```
Server: 位置座標チェック
Server: 場外判定 → プレイヤーリスポーン処理
Server: 死亡回数インクリメント
Server → All Clients: {"type": "respawn", "data": {respawned_player}}
```

## 技術スタック

### バックエンド
- **FastAPI**: 高性能なPython Web API フレームワーク
- **WebSockets**: リアルタイム双方向通信
- **Pydantic**: データバリデーションとシリアライゼーション
- **Uvicorn**: ASGI サーバー

### フロントエンド
- **Pygame**: 2Dゲーム開発ライブラリ
- **asyncio**: 非同期処理
- **websockets**: WebSocket クライアントライブラリ

### 開発・運用
- **Poetry**: Python 依存関係管理
- **Docker**: サーバーのコンテナ化
- **Docker Compose**: 開発環境の構築
- **Pre-commit**: コード品質管理

## スケーラビリティ考慮

### 現在の制限
- 単一サーバーインスタンス
- メモリ内ゲーム状態管理
- 水平スケーリング未対応

### 将来的な拡張案
- Redis を使った状態共有
- ロードバランサーによる複数サーバー対応
- データベースによる永続化
- ゲームルーム機能
- 観戦者モード

## セキュリティ考慮

### 実装済み
- CORS 設定
- 入力データバリデーション
- WebSocket 接続管理

### 今後の改善点
- 認証・認可システム
- レート制限
- 入力値のサニタイズ強化
- SSL/TLS 対応