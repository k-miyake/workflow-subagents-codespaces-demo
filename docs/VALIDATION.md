# 検証記録

検証日: 2026-09-11

## 完了

- Python 3.13 に固定コミットのランタイム `0.1.0b14` と依存パッケージをインストール。`pip check` 成功。
- Ruff によるスクリプトの静的検査。
- 13 件の単体テスト: 3 種類の模擬 PR シナリオ、入力不備・重複・過大 Queue 入力の拒否、秘密情報を設定に保存しないこと、設定優先順位、モデル設定の妥当性、古い ETag を成功としないこと、レポートの HTML / PR URL 検査。
- Azurite 3.35.0 を実際に起動した統合テスト 1 件: Queue の日本語 JSON base64 往復、公式 publisher による Blob 保存、再保存による ETag 変更、Blob が同じ保存先 1 個であること、Content-Type。
- 合計 `14 passed`。統合テストの HTML はテスト専用 fixture であり、モデル生成結果ではない。
- `create_function_app` でサンプルの 6 関数を登録できることを確認。Queue トリガー、ワークフロー orchestrator、tool activity、subagent activity を含む。
- MCR 上の Python / Azurite / DTS イメージ参照の存在を確認。Python と DTS は OCI index digest を固定。

## 未完了

- Codespaces でのコンテナー構築と起動: 実施予定。
- 実モデルへの認証・接続、および Queue → サブエージェント → HTML → Blob の E2E: モデル接続先と認証待ち。
- 実モデルでのワーカー再起動からの継続。

実モデル E2E は Codespaces で `./demo verify --timeout 600` を実行して確認する。DTS と Azurite が動くだけでは動的ワークフローの E2E 成功とは判定しない。
