# Crypto Calculator

暗号資産損益計算システムのリポジトリです。基本的な取引履歴の解析や損益計算、
簡易的なレポート出力を行うためのサンプル実装が含まれています。詳細な開発計画に
ついては `要件定義書.md` を参照してください。

## セットアップ

### CLI版（従来の実装）

1. Python 3.8 以上がインストールされていることを確認してください。
2. このリポジトリをクローン後、以下のコマンドでパッケージをインストールします。

```bash
pip install -e .
```

テストを実行する場合は `test` というオプション依存関係を使用します。

```bash
pip install -e .[test]
pytest
```

### Web版（新実装）

Web版はNext.jsフロントエンドとFastAPIバックエンドで構成されています。

#### バックエンドの起動

```bash
cd backend
pip install -r requirements.txt
python main.py
```

バックエンドは http://localhost:8000 で起動します。

#### フロントエンドの起動

```bash
cd frontend
npm install
npm run dev
```

フロントエンドは http://localhost:3000 で起動します。

## 使い方

### CLI版

コマンドラインツール `crypto-calculator` を用いて、サンプルデータから
損益計算を行い CSV と PDF のレポートを生成できます。

```bash
crypto-calculator output/report --exchange binance --method FIFO
```

上記コマンドでは `output/report.csv` と `output/report.pdf` が作成されます。

取引履歴を CSV から読み込む場合は `--csv` オプションを指定します。

```bash
python -m crypto_calculator.main output/report --csv trades.csv --method FIFO
```

CSV ファイルは以下のような形式を想定しています。

```csv
id,symbol,amount,price,timestamp,side
1,BTCUSDT,0.1,30000,1609459200000,buy
2,BTCUSDT,-0.1,31000,1609462800000,sell
```

### Web版

1. ブラウザで http://localhost:3000 を開きます
2. 新規ユーザー登録またはログインします
3. ダッシュボードで取引を追加または CSV をインポートします
4. 計算方式（FIFO/LIFO）を選択して損益を計算します
5. レポートページから税務用レポートを生成・ダウンロードできます

## Web版の機能

- **認証システム**: ユーザー登録・ログイン機能
- **取引管理**: 手動での取引追加およびCSVインポート
- **損益計算**: FIFO/LIFO方式での自動計算
- **レポート生成**: CSV形式での税務レポート生成
- **リアルタイム計算**: 取引追加時の即時計算表示
- **在庫管理**: 現在の保有状況と平均取得価格の表示

## ディレクトリ構成

- `src/` - パッケージ本体
- `tests/` - テストコード
- `要件定義書.md` - 日本語の要件定義書

## ライセンス

このプロジェクトは MIT ライセンスの下で提供されています。詳細は `LICENSE` を参照してください。
