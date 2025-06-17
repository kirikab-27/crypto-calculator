# Crypto Calculator 🚀

個人投資家向けの暗号資産損益計算システム - 税務申告をシンプルに、正確に。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688.svg)](https://fastapi.tiangolo.com)

## 📋 プロジェクト概要

Crypto Calculatorは、暗号資産投資家が直面する税務計算の複雑さを解決するために開発されたシステムです。複数の取引所での取引データを統合し、日本の税法に準拠した損益計算を自動化します。

### 🎯 解決する課題
- **時間削減**: 手動計算にかかる時間を60-70%削減
- **エラー低減**: 計算ミスを5%未満に抑制
- **簡単操作**: 専門知識なしでポートフォリオ管理が可能

## ✨ 主要機能

### 🔐 ユーザー認証
- JWT認証による安全なアカウント管理
- bcryptによるパスワードハッシュ化
- セッション管理とセキュアなAPI通信

### 📊 取引管理
- **対応取引所**: Binance、MEXC（追加予定）
- **データインポート**: CSV形式での一括取り込み
- **重複防止**: データベースレベルでの一意制約
- **リアルタイム同期**: 取引所APIとの連携

### 💹 損益計算エンジン
- **計算方式**: FIFO（先入先出法）、LIFO（後入先出法）
- **在庫管理**: リアルタイムの保有状況表示
- **平均取得価格**: 自動計算・更新
- **複数通貨対応**: BTC、ETH等主要通貨をサポート

### 📑 レポート生成
- **出力形式**: CSV、PDF、JSON
- **期間指定**: 任意の期間での集計が可能
- **詳細履歴**: 全取引の詳細を含む包括的レポート
- **税務対応**: 確定申告用フォーマット

### 📈 可視化・分析
- **ダッシュボード**: 取引一覧とフィルタリング機能
- **チャート表示**: Rechartsによるデータ可視化
- **パフォーマンス分析**: 損益推移の確認

## 🏗️ アーキテクチャ

```
┌─────────────────────┐     ┌─────────────────────┐
│   Frontend          │────▶│    Backend API      │
│  (Next.js 14/TS)    │     │ (FastAPI/Python)    │
│  - Material-UI      │     │ - JWT Auth          │
│  - Recharts         │     │ - SQLAlchemy        │
└─────────────────────┘     └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │    Database         │
                            │    (SQLite)         │
                            │  - Transactions     │
                            │  - Users            │
                            │  - Reports          │
                            └─────────────────────┘
```

## 🚀 クイックスタート

### 前提条件
- Python 3.8以上
- Node.js 16以上
- npm または yarn

### 簡単セットアップ（推奨）

開発環境を一括で起動：

**Unix/Mac/Linux:**
```bash
git clone https://github.com/kirikab-27/crypto-calculator.git
cd crypto-calculator
./run_dev.sh
```

**Windows:**
```bash
git clone https://github.com/kirikab-27/crypto-calculator.git
cd crypto-calculator
run_dev.bat
```

ブラウザで http://localhost:3000 を開いてアクセスしてください。

## 📖 詳細セットアップ

### バックエンド（FastAPI）

```bash
cd backend
pip install -r requirements.txt

# 開発サーバーの起動
python main.py

# APIドキュメント: http://localhost:8000/docs
```

### フロントエンド（Next.js）

```bash
cd frontend
npm install

# 開発サーバーの起動
npm run dev

# ビルド
npm run build

# 本番サーバーの起動
npm start
```

### データベースの初期化

```bash
cd src
python -m db  # SQLiteデータベースの作成
python -m migrations  # マイグレーションの実行
```

## 🔧 CLI版の使用方法

従来のCLIツールも利用可能です：

```bash
# パッケージのインストール
pip install -e .

# 基本的な使用例
crypto-calculator output/report --exchange binance --method FIFO

# CSVファイルからのインポート
crypto-calculator output/report --csv trades.csv --method LIFO

# ヘルプの表示
crypto-calculator --help
```

### CSV形式

取引データは以下の形式で準備してください：

```csv
id,symbol,amount,price,timestamp,side
1,BTCUSDT,0.1,30000,1609459200000,buy
2,BTCUSDT,-0.1,31000,1609462800000,sell
```

## 🧪 テスト

### バックエンドテスト
```bash
cd backend
pytest
```

### フロントエンドテスト
```bash
cd frontend
npm test
```

### E2Eテスト
```bash
npm run test:e2e
```

## 📁 プロジェクト構造

```
crypto-calculator/
├── backend/            # FastAPIバックエンド
│   ├── main.py        # エントリーポイント
│   └── requirements.txt
│
├── frontend/           # Next.jsフロントエンド
│   ├── app/           # App Router
│   │   ├── dashboard/ # ダッシュボード
│   │   ├── login/     # 認証画面
│   │   └── report/    # レポート生成
│   └── package.json
│
├── src/               # コアロジック・CLIツール
│   ├── auth.py        # 認証処理
│   ├── calculator.py  # 損益計算エンジン
│   ├── db.py          # データベース操作
│   └── reporting.py   # レポート生成
│
├── tests/             # テストスイート
│   ├── test_*.py      # 単体テスト
│   └── integration/   # 統合テスト
│
└── docs/              # ドキュメント
    └── 要件定義書.md   # 詳細仕様
```

## 🛠️ 開発者向け情報

### 環境変数

`.env`ファイルを作成して以下を設定：

```env
# バックエンド
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./crypto_calculator.db
CORS_ORIGINS=http://localhost:3000

# フロントエンド
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### コーディング規約

- **Python**: PEP 8準拠、Black/flake8でフォーマット
- **TypeScript**: ESLint/Prettier設定に従う
- **コミット**: Conventional Commits形式

### API仕様

APIドキュメントは開発サーバー起動後、以下で確認できます：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📅 ロードマップ

### ✅ Phase 1: MVP（完了）
- [x] 基本的な取引管理機能
- [x] FIFO/LIFO損益計算
- [x] CSVインポート/エクスポート
- [x] Web UIの実装
- [x] ユーザー認証システム

### 🚧 Phase 2: 機能拡張（開発中）
- [ ] 追加取引所の統合（Coinbase、Kraken等）
- [ ] 平均原価法・個別識別法の実装
- [ ] DeFi取引のサポート
- [ ] 高度なチャート分析機能
- [ ] モバイルアプリ対応

### 📋 Phase 3: エンタープライズ（計画中）
- [ ] NFT・ゲーム資産の追跡
- [ ] 税金最適化の提案機能
- [ ] 全取引所対応
- [ ] マルチテナント対応
- [ ] 監査ログ機能

## 🤝 コントリビューション

プロジェクトへの貢献を歓迎します！

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/kirikab-27/crypto-calculator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kirikab-27/crypto-calculator/discussions)
- **Email**: support@crypto-calculator.example.com

## 🙏 謝辞

このプロジェクトは以下のオープンソースプロジェクトを使用しています：

- [FastAPI](https://fastapi.tiangolo.com/) - 高速なWebフレームワーク
- [Next.js](https://nextjs.org/) - Reactフレームワーク
- [Material-UI](https://mui.com/) - UIコンポーネント
- [Recharts](https://recharts.org/) - チャートライブラリ

---

**注意**: このプロジェクトは継続的に開発中です。最新の情報については[要件定義書.md](要件定義書.md)もご確認ください。