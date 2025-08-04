# サーバー仕様書

## 概要

FastAPI と WebSocket を使用したリアルタイムマルチプレイヤーゲームサーバーです。プレイヤーの接続管理、ゲーム状態の同期、ゲームロジックの実行を担当します。

## アーキテクチャ

### ファイル構成
```
server/
├── main.py          # FastAPI アプリケーション・WebSocket エンドポイント
├── game_state.py    # ゲームマネージャーとゲームロジック
├── models.py        # Pydantic データモデル
└── Dockerfile       # Docker コンテナ設定
```

## FastAPI アプリケーション (`main.py`)

### エンドポイント

#### WebSocket エンドポイント
- **URL**: `ws://localhost:8000/ws`
- **プロトコル**: WebSocket
- **形式**: JSON メッセージ

#### REST API エンドポイント
- **`GET /`**: サーバー情報を返す
- **`GET /health`**: ヘルスチェック（現在のプレイヤー数を含む）

### WebSocket 接続フロー

1. **接続確立**: クライアントが `/ws` に WebSocket 接続
2. **プレイヤー登録**: `join` メッセージでプレイヤー名を送信
3. **ゲーム状態送信**: サーバーが初期ゲーム状態をクライアントに送信
4. **リアルタイム通信**: 入力・更新メッセージの双方向通信
5. **接続終了**: プレイヤーの削除とブロードキャスト

### CORS 設定
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[\"*\"],
    allow_credentials=True,
    allow_methods=[\"*\"],
    allow_headers=[\"*\"],
)
```

## ゲームマネージャー (`game_state.py`)

### GameManager クラス

#### 初期化パラメータ
```python
self.player_speed = 5.0        # 通常移動速度
self.dash_speed = 15.0         # ダッシュ移動速度
self.dash_duration = 0.3       # ダッシュ継続時間（秒）
self.dash_cooldown = 1.0       # ダッシュクールダウン（秒）
```

#### 主要メソッド

##### プレイヤー管理
- **`add_player(websocket, player_name)`**: 新規プレイヤーの追加
- **`remove_player(player_id)`**: プレイヤーの削除
- **`broadcast_update(update)`**: 全クライアントへのメッセージ配信

##### ゲームロジック
- **`handle_player_input(player_input)`**: プレイヤー入力の処理
- **`move_player(player, direction)`**: プレイヤーの移動処理
- **`dash_player(player, direction, current_time)`**: ダッシュ処理
- **`is_out_of_bounds(player)`**: 場外判定
- **`respawn_player(player)`**: プレイヤーのリスポーン

### ゲームフィールド設定
```python
field_width: int = 800    # フィールド幅（ピクセル）
field_height: int = 600   # フィールド高さ（ピクセル）
player_size: int = 30     # プレイヤーサイズ（ピクセル）
```

### 移動ロジック

#### 通常移動
- 移動速度: 5.0 ピクセル/フレーム
- フィールド境界での衝突判定
- 座標クランプ処理

#### ダッシュ移動
- 移動速度: 15.0 ピクセル/フレーム
- 移動距離: `dash_speed * 3` = 45 ピクセル
- フィールド外への移動許可（-50 〜 +50 ピクセル）
- 0.3秒後に自動的にダッシュ状態解除

#### 場外判定
```python
def is_out_of_bounds(self, player: Player) -> bool:
    return (player.x < -self.state.player_size or 
            player.x > self.state.field_width or
            player.y < -self.state.player_size or 
            player.y > self.state.field_height)
```

#### リスポーン処理
- スポーン位置: フィールド中央 `(400, 300)`
- 死亡回数のインクリメント
- ダッシュ状態の解除

## データモデル (`models.py`)

### Player モデル
```python
class Player(BaseModel):
    id: str                          # UUID（自動生成）
    name: str                        # プレイヤー名
    x: float                         # X座標
    y: float                         # Y座標
    color: Tuple[int, int, int]      # RGB色値（自動生成）
    deaths: int = 0                  # 死亡回数
    is_dashing: bool = False         # ダッシュ状態
    dash_cooldown: float = 0.0       # ダッシュクールダウン時刻
```

#### 色の自動生成
```python
data['color'] = (
    random.randint(50, 255),  # R値: 50-255
    random.randint(50, 255),  # G値: 50-255
    random.randint(50, 255)   # B値: 50-255
)
```

### GameState モデル
```python
class GameState(BaseModel):
    players: Dict[str, Player] = {}  # プレイヤー辞書
    field_width: int = 800           # フィールド幅
    field_height: int = 600          # フィールド高さ
    player_size: int = 30            # プレイヤーサイズ
```

### PlayerInput モデル
```python
class PlayerInput(BaseModel):
    player_id: str                   # プレイヤーID
    action: str                      # \"move\" または \"dash\"
    direction: str = None            # \"up\", \"down\", \"left\", \"right\"
```

### GameUpdate モデル
```python
class GameUpdate(BaseModel):
    type: str                        # メッセージタイプ
    data: Dict                       # ペイロードデータ
```

## Docker 設定

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Poetry のインストール
RUN pip install poetry==1.6.1

# 依存関係のインストール
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \\
    && poetry install --only=main --no-dev

# アプリケーションコードのコピー
COPY server/ ./

EXPOSE 8000

CMD [\"python\", \"main.py\"]
```

### Docker Compose 設定
```yaml
version: '3.8'

services:
  game-server:
    build:
      context: .
      dockerfile: ./server/Dockerfile
    ports:
      - \"8000:8000\"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

## 開発・デバッグ

### 直接実行
```bash
# Poetry 環境でサーバー起動
poetry run python server/main.py

# サーバーは localhost:8000 でリッスン
```

### ログ出力
- プレイヤー接続・切断時のコンソールログ
- WebSocket エラーのキャッチとログ出力
- 死活監視用の接続数表示

### ヘルスチェック
```bash
# サーバー状態の確認
curl http://localhost:8000/health

# レスポンス例
{\"status\": \"healthy\", \"players\": 3}
```

## パフォーマンス特性

### 制限事項
- 同時接続プレイヤー数: 理論上無制限（実用的には10-20人程度）
- メッセージ配信: O(n) の全プレイヤーブロードキャスト
- 状態管理: メモリ内のみ（永続化なし）

### 最適化ポイント
- 不要な位置更新の削除
- 死活監視による接続クリーンアップ
- 非同期処理による高いスループット