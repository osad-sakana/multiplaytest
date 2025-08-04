# ゲームロジック仕様書

## 概要

マルチプレイヤーゲームのゲームルール、物理演算、および各種システムの詳細な動作仕様です。

## ゲームフィールド

### フィールド設定
```python
FIELD_WIDTH = 800      # フィールド幅（ピクセル）
FIELD_HEIGHT = 600     # フィールド高さ（ピクセル）
PLAYER_SIZE = 30       # プレイヤーサイズ（正方形、ピクセル）
```

### 座標系
- **原点**: 左上角 `(0, 0)`
- **X軸**: 右方向が正
- **Y軸**: 下方向が正
- **範囲**: `(0, 0)` から `(800, 600)`

### フィールド境界
- **表示境界**: `(0, 0)` - `(800, 600)`
- **移動可能範囲**: `(0, 0)` - `(770, 570)` （プレイヤーサイズ考慮）
- **場外判定範囲**: プレイヤー中心が `-30` - `830` (X軸), `-30` - `630` (Y軸) 外

## プレイヤーシステム

### プレイヤー生成
```python
def create_player(name: str) -> Player:
    return Player(
        id=str(uuid.uuid4()),           # 一意のUUID
        name=name,                      # プレイヤー名
        x=400.0,                        # 初期X座標（中央）
        y=300.0,                        # 初期Y座標（中央）
        color=generate_random_color(),  # ランダム色
        deaths=0,                       # 死亡回数
        is_dashing=False,               # ダッシュ状態
        dash_cooldown=0.0               # クールダウン時刻
    )
```

### 色生成システム
```python
def generate_random_color() -> Tuple[int, int, int]:
    return (
        random.randint(50, 255),  # R値: 暗すぎる色を避ける
        random.randint(50, 255),  # G値: 暗すぎる色を避ける  
        random.randint(50, 255)   # B値: 暗すぎる色を避ける
    )
```

### スポーン・リスポーン
- **初期スポーン位置**: フィールド中央 `(400, 300)`
- **リスポーン位置**: フィールド中央 `(400, 300)`
- **リスポーン条件**: 場外判定時
- **リスポーン効果**: 死亡回数+1、ダッシュ状態解除

## 移動システム

### 基本移動
```python
NORMAL_SPEED = 5.0      # 通常移動速度（ピクセル/フレーム）
```

#### 移動処理
```python
def move_player(player: Player, direction: str):
    if direction == \"up\":
        player.y = max(0, player.y - NORMAL_SPEED)
    elif direction == \"down\":
        player.y = min(FIELD_HEIGHT - PLAYER_SIZE, player.y + NORMAL_SPEED)
    elif direction == \"left\":
        player.x = max(0, player.x - NORMAL_SPEED)
    elif direction == \"right\":
        player.x = min(FIELD_WIDTH - PLAYER_SIZE, player.x + NORMAL_SPEED)
```

#### 境界クランプ
- プレイヤーはフィールド境界を超えて移動できません
- 境界に達すると、それ以上の移動は無効化されます

### ダッシュシステム

#### ダッシュ設定
```python
DASH_SPEED = 15.0           # ダッシュ速度（ピクセル/フレーム）
DASH_DISTANCE = 45.0        # ダッシュ距離（DASH_SPEED × 3）
DASH_DURATION = 0.3         # ダッシュ継続時間（秒）
DASH_COOLDOWN = 1.0         # ダッシュクールダウン（秒）
```

#### ダッシュ実行条件
```python
def can_dash(player: Player) -> bool:
    current_time = time.time()
    return player.dash_cooldown <= current_time
```

#### ダッシュ処理
```python
def dash_player(player: Player, direction: str, current_time: float):
    if not can_dash(player):
        return
    
    player.is_dashing = True
    player.dash_cooldown = current_time + DASH_COOLDOWN
    
    # ダッシュ移動（境界を超えて移動可能）
    if direction == \"up\":
        player.y = max(-50, player.y - DASH_DISTANCE)
    elif direction == \"down\":
        player.y = min(FIELD_HEIGHT + 50, player.y + DASH_DISTANCE)
    elif direction == \"left\":
        player.x = max(-50, player.x - DASH_DISTANCE)
    elif direction == \"right\":
        player.x = min(FIELD_WIDTH + 50, player.x + DASH_DISTANCE)
    
    # ダッシュ状態の自動解除をスケジュール
    schedule_dash_end(player, DASH_DURATION)
```

#### ダッシュ状態解除
```python
async def end_dash(player: Player):
    await asyncio.sleep(DASH_DURATION)
    player.is_dashing = False
    broadcast_player_update(player)
```

## 衝突・場外判定システム

### 場外判定
```python
def is_out_of_bounds(player: Player) -> bool:
    return (
        player.x < -PLAYER_SIZE or           # 左端を超えた
        player.x > FIELD_WIDTH or           # 右端を超えた  
        player.y < -PLAYER_SIZE or           # 上端を超えた
        player.y > FIELD_HEIGHT              # 下端を超えた
    )
```

### 場外判定のタイミング
- 通常移動後: 境界クランプにより場外になることはない
- ダッシュ移動後: 勢い余って場外に出る可能性がある

### 場外処理フロー
```python
def handle_out_of_bounds(player: Player):
    if is_out_of_bounds(player):
        player.x = 400.0                    # 中央X座標
        player.y = 300.0                    # 中央Y座標
        player.deaths += 1                  # 死亡回数増加
        player.is_dashing = False           # ダッシュ状態解除
        broadcast_respawn(player)           # 全プレイヤーに通知
```

## スコアリングシステム

### スコア計算
- **基本スコア**: 死亡回数（少ないほど良い）
- **順位決定**: 死亡回数の昇順でソート
- **同点時**: 参加順（先着優先）

### ランキング表示
```python
def get_leaderboard(players: Dict[str, Player]) -> List[Tuple[str, Player]]:
    return sorted(
        players.items(),
        key=lambda x: (x[1].deaths, x[1].id)  # 死亡回数, ID順
    )
```

## 物理演算

### フレームレート
- **サーバー**: 非同期処理（入力駆動）
- **クライアント**: 60 FPS
- **同期**: 入力時のリアルタイム同期

### 座標精度
- **内部計算**: 浮動小数点（`float`）
- **描画**: 整数座標への変換
- **通信**: 浮動小数点で送信

### タイムスタンプ
```python
import time

current_time = time.time()          # UNIX timestamp（秒）
player.dash_cooldown = current_time + DASH_COOLDOWN
```

## ゲーム状態管理

### 状態同期
- **イベント駆動**: プレイヤーの行動時のみ同期
- **ブロードキャスト**: 全プレイヤーに状態変更を通知
- **権威サーバー**: サーバーが最終的な状態を決定

### 状態の種類

#### プレイヤー状態
- **位置**: `(x, y)` 座標
- **色**: RGB値（変更不可）
- **名前**: プレイヤー名（変更不可）
- **統計**: 死亡回数
- **一時状態**: ダッシュ状態、クールダウン

#### ゲーム状態
- **プレイヤーリスト**: 接続中の全プレイヤー
- **フィールド設定**: サイズ、境界
- **ゲーム設定**: 移動速度、ダッシュ設定

## ゲームルール詳細

### 勝利条件
- **明示的な勝利条件なし**: エンドレスゲーム
- **競争要素**: 死亡回数による順位

### プレイヤー制限
- **最大プレイヤー数**: 理論上無制限（実用的には10-20人）
- **最小プレイヤー数**: 1人（一人でもプレイ可能）
- **同じ名前**: 許可（IDで区別）

### ゲーム進行
1. **参加**: いつでも参加・離脱可能
2. **プレイ**: リアルタイムで移動・ダッシュ
3. **場外**: 落下したらリスポーン
4. **継続**: エンドレスゲーム

## バランス調整

### 現在の設定値
```python
# 移動関連
NORMAL_SPEED = 5.0      # 安全な移動速度
DASH_SPEED = 15.0       # 3倍速（リスキー）
DASH_DISTANCE = 45.0    # 大きな移動距離

# タイミング関連  
DASH_DURATION = 0.3     # 短時間の制御不能
DASH_COOLDOWN = 1.0     # 適度な待機時間

# フィールド関連
FIELD_SIZE = 800x600    # 適度な広さ
PLAYER_SIZE = 30        # 視認しやすいサイズ
```

### 調整可能なパラメータ
- **移動速度**: ゲームペースの調整
- **ダッシュ距離**: リスクとリターンのバランス
- **クールダウン時間**: ダッシュの使用頻度制御
- **フィールドサイズ**: 混雑度の調整

## デバッグ・テスト用機能

### ログ出力
- プレイヤー参加・離脱
- 場外判定とリスポーン
- WebSocket接続エラー

### 開発者向け情報
- プレイヤー座標の表示
- ダッシュ状態の可視化
- 接続数の監視