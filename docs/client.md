# クライアント仕様書

## 概要

Pygame を使用したゲームクライアントです。サーバーとの WebSocket 通信、ユーザー入力処理、ゲーム画面の描画を担当します。

## アーキテクチャ

### ファイル構成
```
client/
├── main.py          # メインゲームループとイベント処理
├── game_client.py   # WebSocket 通信管理
└── renderer.py      # Pygame 描画エンジン
```

## メインゲームループ (`main.py`)

### Game クラス

#### 初期化
```python
def __init__(self):
    self.client = AsyncGameClient()      # WebSocket クライアント
    self.renderer = GameRenderer()       # 描画エンジン
    self.running = True                  # ゲームループ制御
    self.connected = False               # 接続状態
    self.game_state = {}                 # ゲーム状態
```

#### 状態管理

##### 接続画面状態
```python
self.connection_screen = True           # 接続画面表示フラグ
self.server_input = \"localhost\"        # サーバーアドレス入力
self.port_input = \"8000\"               # ポート番号入力
self.name_input = \"Player\"             # プレイヤー名入力
self.current_field = 0                  # 現在のフォーカスフィールド
self.error_message = \"\"               # エラーメッセージ
```

##### ゲーム入力状態
```python
self.keys_pressed = set()               # 現在押下中のキー
self.dash_keys = {pygame.K_LSHIFT, pygame.K_RSHIFT}  # ダッシュキー
```

### イベント処理

#### 接続画面での入力処理
```python
def handle_connection_input(self, event):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_TAB:
            self.current_field = (self.current_field + 1) % 3  # フィールド切り替え
        elif event.key == pygame.K_BACKSPACE:
            # 現在のフィールドから文字削除
        elif event.key == pygame.K_RETURN:
            self.attempt_connection()  # 接続試行
        else:
            # 文字入力の処理
```

#### ゲーム画面での入力処理
```python
def handle_game_input(self, event):
    if event.type == pygame.KEYDOWN:
        self.keys_pressed.add(event.key)
        if event.key == pygame.K_ESCAPE:
            self.running = False  # ゲーム終了
    elif event.type == pygame.KEYUP:
        self.keys_pressed.discard(event.key)
```

### 移動処理
```python
def process_movement(self):
    # ダッシュ判定
    is_dashing = any(key in self.keys_pressed for key in self.dash_keys)
    action = \"dash\" if is_dashing else \"move\"
    
    # 方向キーの処理（WASD）
    if pygame.K_w in self.keys_pressed:  # 上
        self.client.send_input(action, \"up\")
    if pygame.K_s in self.keys_pressed:  # 下
        self.client.send_input(action, \"down\")
    if pygame.K_a in self.keys_pressed:  # 左
        self.client.send_input(action, \"left\")
    if pygame.K_d in self.keys_pressed:  # 右
        self.client.send_input(action, \"right\")
```

### サーバーメッセージハンドラー

#### ゲーム状態更新
```python
def _handle_game_state(self, data):
    self.game_state = data.get(\"data\", {})

def _handle_player_update(self, data):
    player_data = data.get(\"data\", {}).get(\"player\", {})
    player_id = player_data.get(\"id\")
    if player_id and \"players\" in self.game_state:
        self.game_state[\"players\"][player_id] = player_data
```

#### プレイヤー参加・離脱
```python
def _handle_player_joined(self, data):
    player_data = data.get(\"data\", {}).get(\"player\", {})
    # プレイヤーをゲーム状態に追加

def _handle_player_left(self, data):
    player_id = data.get(\"data\", {}).get(\"player_id\")
    # プレイヤーをゲーム状態から削除
```

## WebSocket 通信 (`game_client.py`)

### AsyncGameClient クラス

#### スレッド管理
```python
def start_client_thread(self):
    self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
    self.thread.start()

def _run_event_loop(self):
    self.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self.loop)
    self.loop.run_forever()
```

#### 接続管理
```python
def connect(self, server_url: str, player_name: str, callback: Callable = None):
    # 非同期接続をスレッドセーフに実行
    future = asyncio.run_coroutine_threadsafe(
        self.client.connect(server_url, player_name), self.loop
    )
    return future.result(timeout=5.0)
```

#### メッセージ送信
```python
def send_input(self, action: str, direction: str = None):
    if self.loop and self.client.connected:
        asyncio.run_coroutine_threadsafe(
            self.client.send_input(action, direction), self.loop
        )
```

### GameClient クラス（内部実装）

#### WebSocket 接続
```python
async def connect(self, server_url: str, player_name: str) -> bool:
    self.websocket = await websockets.connect(server_url)
    self.connected = True
    
    # 参加メッセージ送信
    join_message = {\"type\": \"join\", \"name\": player_name}
    await self.websocket.send(json.dumps(join_message))
```

#### メッセージ受信ループ
```python
async def _receive_messages(self):
    while self.connected and self.websocket:
        message = await self.websocket.recv()
        data = json.loads(message)
        
        message_type = data.get(\"type\")
        
        # 登録されたハンドラーを呼び出し
        if message_type in self.message_handlers:
            self.message_handlers[message_type](data)
```

## 描画エンジン (`renderer.py`)

### GameRenderer クラス

#### 初期化設定
```python
def __init__(self, width: int = 800, height: int = 600):
    pygame.init()
    self.width = width
    self.height = height
    self.screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(\"Multiplayer Game\")
    
    # フォントとカラーの設定
    self.font = pygame.font.Font(None, 36)
    self.small_font = pygame.font.Font(None, 24)
```

### ゲーム画面描画

#### メイン描画ループ
```python
def render_game(self, game_state: Dict, player_id: str):
    self.screen.fill(self.BLACK)  # 背景クリア
    
    # フィールド境界線描画
    pygame.draw.rect(self.screen, self.WHITE, (0, 0, field_width, field_height), 2)
    
    # プレイヤー描画
    for pid, player_data in players.items():
        self._render_player(player_data, player_size, pid == player_id)
    
    # UI描画
    self._render_ui(players, player_id)
    
    pygame.display.flip()
```

#### プレイヤー描画
```python
def _render_player(self, player_data: Dict, player_size: int, is_current_player: bool):
    x, y = int(player_data.get(\"x\", 0)), int(player_data.get(\"y\", 0))
    color = player_data.get(\"color\", (255, 255, 255))
    is_dashing = player_data.get(\"is_dashing\", False)
    
    # ダッシュエフェクト
    if is_dashing:
        pygame.draw.rect(self.screen, (255, 255, 255), 
                        player_rect.inflate(6, 6))
    
    # プレイヤー四角形
    pygame.draw.rect(self.screen, color, player_rect)
    
    # 現在プレイヤーの境界線
    if is_current_player:
        pygame.draw.rect(self.screen, self.WHITE, player_rect, 3)
```

#### スコアボード描画
```python
def _render_ui(self, players: Dict, player_id: str):
    # 死亡回数順でソート
    sorted_players = sorted(players.items(), key=lambda x: x[1].get(\"deaths\", 0))
    
    for i, (pid, player_data) in enumerate(sorted_players):
        name = player_data.get(\"name\", \"Unknown\")
        deaths = player_data.get(\"deaths\", 0)
        
        # 現在プレイヤーをハイライト
        text_color = self.GREEN if pid == player_id else self.WHITE
        
        # スコア表示
        score_text = f\"{name}: {deaths}\"
        score_surface = self.small_font.render(score_text, True, text_color)
```

### 接続画面描画

#### 入力フィールド
```python
def render_connection_screen(self, server_input: str, port_input: str, 
                           name_input: str, error_message: str = \"\"):
    # タイトル表示
    title_surface = self.font.render(\"Connect to Server\", True, self.WHITE)
    
    # 入力フィールド（Server IP, Port, Name）
    fields = [
        (\"Server IP:\", server_input, 200),
        (\"Port:\", port_input, 250),
        (\"Your Name:\", name_input, 300)
    ]
    
    for label, value, y_pos in fields:
        # ラベルと入力ボックスの描画
```

## 設定可能な値

### デフォルト接続設定
```python
self.server_input = \"localhost\"  # サーバーアドレス
self.port_input = \"8000\"         # ポート番号
self.name_input = \"Player\"       # プレイヤー名
```

### フレームレート
```python
clock.tick(60)  # 60 FPS
```

### キーマッピング
```python
# 移動キー
pygame.K_w  # 上
pygame.K_a  # 左
pygame.K_s  # 下
pygame.K_d  # 右

# ダッシュキー
pygame.K_LSHIFT  # 左Shift
pygame.K_RSHIFT  # 右Shift

# システムキー
pygame.K_ESCAPE  # ゲーム終了
pygame.K_TAB     # フィールド切り替え（接続画面）
```

## エラーハンドリング

### 接続エラー
- タイムアウト: 5秒でタイムアウト
- 無効なポート番号: バリデーションエラー表示
- サーバー未接続: 接続失敗メッセージ表示

### 通信エラー
- WebSocket切断: 自動的に接続画面に戻る
- メッセージ送信失敗: 接続状態をfalseに設定