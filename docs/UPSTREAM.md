# 出典と変更点

確認日: 2026-09-11

- 公式リポジトリ: https://github.com/Azure/azure-functions-agents-runtime
- 固定コミット: `3ab9e8d9b9749c2a4ad15f65703a13255fbecb2b`（2026-09-09）
- サンプル: `samples/workflow-subagents-preview`
- 取得時のランタイムバージョン: `0.1.0b14`
- 原ライセンス: [MIT](../LICENSE.md)
- 元 README: [UPSTREAM_README.md](UPSTREAM_README.md)

## サンプルからの変更

1. `src/requirements.txt` の `-e ../../..` を上記コミットの Git URL に置換し、単独リポジトリで導入可能にした。
2. `src/local.settings.template.json` のモデル初期値を空欄にし、実在するデプロイ名の指定を必須化した。
3. レポートライターに日本語での出力と「模擬データ」の明示を指示した。
4. 公式 `scripts/verify.py` を `scripts/verify_upstream.py` として同梱。エミュレーターの参照を本デモと同じものに固定した。
5. Codespaces、Docker Compose、設定・起動・Queue 投入・レポート閲覧用コマンド、テスト、日本語手順を追加した。
6. `UseDevelopmentStorage=true` は Python Storage SDK が展開しないため、Azurite の完全な接続文字列をテンプレートに指定した。含まれるキーは Azurite が公表するエミュレーター専用キーであり、Azure リソースの認証情報ではない。実際の Queue/Blob テストで検証した。
7. 起動前に入力 Queue を作成して、初回投入前の QueueNotFound ログを防止した。
8. Codespaces ビルドで確認した、ベースイメージに含まれる未使用 Yarn apt フィードの署名エラーを、当該フィードの除去で解消した。

エージェントの分離、ワークフロー生成・実行、模擬 PR ツール、Blob 出力は公式ランタイムと公式サンプルに依存する。独自の静的オーケストレーターや模擬モデルで置き換えていない。

## コンテナーの固定

- Python: `mcr.microsoft.com/devcontainers/python:1-3.13-bookworm` を OCI index digest `sha256:0aa711e570b306c02946cdda67587ce8c65978dbb65691341cbcfd4854dfcfff` に固定
- DTS: 取得時の `mcr.microsoft.com/dts/dts-emulator:latest` を OCI index digest `sha256:361323065a608d605f9d3ae56b854eb11f1c47fcc16845a37f948f03ca9c5fac` に固定
- Azurite: `3.35.0`
- Functions Core Tools は Microsoft Debian 12 フィードの v4、devcontainer features はメジャーバージョン指定。Python の間接依存も含めた完全な再現性は保証していない。更新時は Codespaces で再ビルドと E2E の再実行が必要。
