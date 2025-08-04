# 配置・運用仕様書

## 概要

Docker を使用したサーバーの配置・運用方法と、クライアントの配布・実行方法について説明します。

## サーバー配置

### Docker 環境での配置

#### 必要な環境
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **メモリ**: 最小 512MB、推奨 1GB+
- **CPU**: 1コア以上
- **ネットワーク**: ポート 8000 の開放

#### 基本的な配置手順

##### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd multiplaytest
```

##### 2. Docker Compose での起動
```bash
# フォアグラウンドで起動（ログ確認用）
docker-compose up --build

# バックグラウンドで起動（本番用）
docker-compose up -d --build

# ログの確認
docker-compose logs -f game-server

# サービスの停止
docker-compose down
```

##### 3. ヘルスチェック
```bash
# サーバーの動作確認
curl http://localhost:8000/health

# 期待されるレスポンス
{\"status\": \"healthy\", \"players\": 0}
```

### Docker 設定詳細

#### Dockerfile 解説
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Poetry のインストール
RUN pip install poetry==1.6.1

# 依存関係設定ファイルのコピー
COPY pyproject.toml poetry.lock* ./

# 本番用依存関係のみインストール
RUN poetry config virtualenvs.create false \\
    && poetry install --only=main --no-dev

# アプリケーションコードのコピー
COPY server/ ./

EXPOSE 8000

CMD [\"python\", \"main.py\"]
```

#### Docker Compose 設定
```yaml
version: '3.8'

services:
  game-server:
    build:
      context: .                    # ルートディレクトリをコンテキストに
      dockerfile: ./server/Dockerfile
    ports:
      - \"8000:8000\"               # ホストポート:コンテナポート
    environment:
      - PYTHONUNBUFFERED=1          # Python ログの即座出力
    restart: unless-stopped         # 自動再起動
```

### 本番環境での配置

#### システム要件
- **OS**: Linux (Ubuntu 20.04+ 推奨)
- **メモリ**: 1GB+ (プレイヤー数に応じて増加)
- **ストレージ**: 1GB+ (ログ用)
- **ネットワーク**: 外部からポート8000へのアクセス許可

#### 環境変数設定
```bash
# .env ファイルの作成
cat > .env << EOF
PYTHONUNBUFFERED=1
PORT=8000
HOST=0.0.0.0
EOF
```

#### Systemd サービス設定（オプション）
```bash
# /etc/systemd/system/multiplaytest.service
[Unit]
Description=Multiplayer Game Server
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/multiplaytest
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

#### サービスの有効化
```bash
sudo systemctl enable multiplaytest
sudo systemctl start multiplaytest
sudo systemctl status multiplaytest
```

### リバースプロキシ設定（Nginx）

#### SSL 対応の WebSocket プロキシ
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # WebSocket プロキシ設定
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket タイムアウト設定
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
    
    # REST API プロキシ設定
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## クライアント配布

### 開発環境でのクライアント実行

#### Poetry 環境での実行
```bash
# 依存関係のインストール
poetry install

# クライアントの起動
poetry run python client/main.py

# または仮想環境をアクティベート
poetry shell
python client/main.py
```

### スタンドアローン実行ファイルの作成

#### PyInstaller を使用した実行ファイル作成
```bash
# PyInstaller のインストール
pip install pyinstaller

# 実行ファイルの作成（Windows）
pyinstaller --onefile --windowed client/main.py

# 実行ファイルの作成（macOS/Linux）
pyinstaller --onefile client/main.py

# 出力先: dist/main.exe (Windows) または dist/main (Unix)
```

#### PyInstaller 設定ファイル（main.spec）
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['client/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pygame',
        'websockets',
        'asyncio'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MultiplayGame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI アプリケーション
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

### クロスプラットフォーム配布

#### 各プラットフォーム向けビルド
```bash
# Windows (from Windows)
pyinstaller main.spec

# macOS (from macOS)  
pyinstaller main.spec

# Linux (from Linux)
pyinstaller main.spec
```

#### GitHub Actions での自動ビルド
```yaml
name: Build Executables

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install
    
    - name: Build executable
      run: |
        poetry run pyinstaller main.spec
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: game-client-${{ matrix.os }}
        path: dist/
```

## 監視・ログ

### ログ管理

#### Docker ログの確認
```bash
# リアルタイムログ表示
docker-compose logs -f game-server

# 過去24時間のログ
docker-compose logs --since 24h game-server

# ログファイルへの出力
docker-compose logs game-server > game-server.log 2>&1
```

#### ログローテーション設定
```json
{
  \"log-driver\": \"json-file\",
  \"log-opts\": {
    \"max-size\": \"10m\",
    \"max-file\": \"3\"
  }
}
```

### モニタリング

#### 基本的なヘルスチェック
```bash
#!/bin/bash
# health-check.sh

URL=\"http://localhost:8000/health\"
RESPONSE=$(curl -s $URL)

if echo $RESPONSE | grep -q '\"status\": \"healthy\"'; then
    echo \"Server is healthy\"
    exit 0
else
    echo \"Server is unhealthy: $RESPONSE\"
    exit 1
fi
```

#### プロメテウス監視（将来的な拡張）
```python
# server/metrics.py (将来的な実装例)
from prometheus_client import Counter, Histogram, Gauge

CONNECTED_PLAYERS = Gauge('connected_players_total', 'Number of connected players')
MESSAGE_COUNT = Counter('messages_total', 'Total number of messages', ['type'])
RESPONSE_TIME = Histogram('response_time_seconds', 'Response time in seconds')
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. ポート競合エラー
```bash
# ポート使用状況の確認
lsof -i :8000
netstat -tulpn | grep :8000

# プロセスの終了
kill -9 <PID>

# Docker コンテナの強制停止
docker-compose down --remove-orphans
```

#### 2. WebSocket 接続エラー
```bash
# ファイアウォール設定の確認
sudo ufw status
sudo ufw allow 8000

# Docker ネットワーク設定の確認
docker network ls
docker network inspect multiplaytest_default
```

#### 3. メモリ不足
```bash
# メモリ使用量の確認
docker stats

# Docker コンテナのメモリ制限
docker-compose.yml に memory: 1g を追加
```

#### 4. SSL/TLS 設定エラー
```bash
# 証明書の確認
openssl x509 -in certificate.crt -text -noout

# Nginx 設定のテスト
sudo nginx -t

# Let's Encrypt 証明書の取得
sudo certbot --nginx -d your-domain.com
```

## セキュリティ考慮事項

### 基本的なセキュリティ設定
- **ファイアウォール**: 必要なポートのみ開放
- **SSL/TLS**: HTTPS/WSS 通信の使用
- **レート制限**: 過度なリクエストの制限
- **入力検証**: クライアント入力の検証

### 今後の改善案
- 認証システムの実装
- DDoS 攻撃対策
- ログ監視システム
- 脆弱性スキャン