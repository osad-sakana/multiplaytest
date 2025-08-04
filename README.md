# マルチプレイゲーム

PygameとFastAPIを使ったリアルタイムマルチプレイヤーゲームです。プレイヤーは色とりどりの四角形を操作して戦場を駆け回り、ダッシュで勢いよく移動できますが、場外に落ちるとリスポーンします。落ちた回数がスコアとして記録される、シンプルながら奥深いゲームです。

## 🎮 ゲームの特徴

- **リアルタイムマルチプレイ**: WebSocketを使った即座の同期
- **ユニークなプレイヤー**: 各プレイヤーに自動割り当てされるランダム色
- **ダッシュシステム**: 高速移動とリスクのバランス
- **競技性**: 落下回数による順位システム
- **簡単接続**: サーバーアドレス入力だけで参加可能

## 📋 必要環境

- **Python**: 3.11以上
- **Poetry**: 依存関係管理
- **Docker & Docker Compose**: サーバー実行用

## 🚀 クイックスタート

### 1. 環境セットアップ
```bash
# リポジトリをクローン
git clone <repository-url>
cd multiplaytest

# 依存関係をインストール
poetry install

# 開発用ツールも含める場合
poetry install --with dev
```

### 2. サーバー起動
```bash
# Dockerでサーバーを起動
docker-compose up --build

# バックグラウンドで起動
docker-compose up -d --build
```

### 3. ゲーム参加
```bash
# クライアントを起動
poetry run python client/main.py

# または仮想環境をアクティベート
poetry shell
python client/main.py
```

### 4. ゲーム接続
1. クライアント起動後、接続画面が表示されます
2. **サーバーIP**: `localhost`（デフォルト）
3. **ポート**: `8000`（デフォルト）
4. **プレイヤー名**: お好みの名前を入力
5. **Enter**キーで接続開始

## 🎯 操作方法

| キー | 機能 |
|------|------|
| **W** | 上に移動 |
| **A** | 左に移動 |
| **S** | 下に移動 |
| **D** | 右に移動 |
| **Shift + WASD** | ダッシュ（高速移動） |
| **ESC** | ゲーム終了 |
| **TAB** | 接続画面でフィールド切り替え |

## 🏆 ゲームルール

- プレイヤーは**30×30ピクセルの四角形**として表示
- **ダッシュ**で素早く移動できるが、制御が難しく場外に落ちやすい
- **場外に落下**すると中央にリスポーン、**落下回数**が1増加
- **スコアボード**で落下回数の少ない順にランキング表示
- **リアルタイム同期**で他プレイヤーの動きが即座に反映

## 🛠 開発者向け

### サーバー開発モード
```bash
# サーバーを直接起動（Dockerなし）
poetry run python server/main.py

# Pre-commitフックをセットアップ
poetry run pre-commit install
```

### コード品質チェック
```bash
# フォーマットと静的解析
poetry run black .
poetry run flake8 .
poetry run isort .

# 全てのpre-commitフックを実行
poetry run pre-commit run --all-files
```

## 📁 プロジェクト構造

```
multiplaytest/
├── server/                 # FastAPIサーバー
│   ├── main.py            # WebSocketエンドポイント
│   ├── game_state.py      # ゲーム状態管理
│   ├── models.py          # データモデル
│   └── Dockerfile         # Docker設定
├── client/                # Pygameクライアント
│   ├── main.py           # メインゲームループ
│   ├── game_client.py    # WebSocket通信
│   └── renderer.py       # 描画処理
├── docs/                 # 仕様書（詳細は下記参照）
├── pyproject.toml        # Poetry設定・依存関係
├── .pre-commit-config.yaml # Pre-commit設定
├── docker-compose.yml    # Docker Compose設定
├── CLAUDE.md            # AI開発者向けガイド
└── README.md            # このファイル
```

## 📚 詳細仕様書

機能ごとの詳細な仕様書は以下をご参照ください：

- **[アーキテクチャ概要](docs/architecture.md)** - システム全体の設計と構成
- **[サーバー仕様](docs/server.md)** - FastAPI WebSocketサーバーの詳細
- **[クライアント仕様](docs/client.md)** - Pygameクライアントの実装
- **[通信プロトコル](docs/protocol.md)** - WebSocket通信の仕様
- **[ゲームロジック](docs/game-logic.md)** - ゲームルールと物理演算
- **[配置・運用](docs/deployment.md)** - Docker環境での配置方法

## 🌐 API エンドポイント

### WebSocket
- `ws://localhost:8000/ws` - ゲーム通信用WebSocketエンドポイント

### REST API
- `GET /` - サーバー情報の取得
- `GET /health` - ヘルスチェック（プレイヤー数含む）

## 🤝 コントリビューション

プロジェクトへの貢献を歓迎します！

1. フォークしてブランチを作成
2. 変更を実装し、テストを実行
3. Pre-commitフックでコード品質をチェック
4. プルリクエストを作成

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🆘 サポート

質問や問題がある場合は、GitHubのIssuesでお知らせください。