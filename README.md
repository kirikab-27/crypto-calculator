# Crypto Calculator

暗号資産損益計算システムのリポジトリです。基本的な取引履歴の解析や損益計算、
簡易的なレポート出力を行うためのサンプル実装が含まれています。詳細な開発計画に
ついては `要件定義書.md` を参照してください。

## セットアップ

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

## 使い方

コマンドラインツール `crypto-calculator` を用いて、サンプルデータから
損益計算を行い CSV と PDF のレポートを生成できます。

```bash
python -m crypto_calculator.main output/report --exchange binance --method FIFO
```

上記コマンドでは `output/report.csv` と `output/report.pdf` が作成されます。

## ディレクトリ構成

- `src/` - パッケージ本体
- `tests/` - テストコード
- `要件定義書.md` - 日本語の要件定義書

## ライセンス

このプロジェクトは MIT ライセンスの下で提供されています。詳細は `LICENSE` を参照してください。
