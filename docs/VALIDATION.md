# 検証記録

検証日: 2026-09-11–12（日本時間）

## 完了

- Python 3.13 に固定コミットのランタイム `0.1.0b14` と依存パッケージをインストール。`pip check` 成功。
- Ruff によるスクリプトの静的検査。
- 13 件の単体テスト: 3 種類の模擬 PR シナリオ、入力不備・重複・過大 Queue 入力の拒否、秘密情報を設定に保存しないこと、設定優先順位、モデル設定の妥当性、古い ETag を成功としないこと、レポートの HTML / PR URL 検査。
- Azurite 3.35.0 を実際に起動した統合テスト 1 件: Queue の日本語 JSON base64 往復、公式 publisher による Blob 保存、再保存による ETag 変更、Blob が同じ保存先 1 個であること、Content-Type。
- 合計 `14 passed`。統合テストの HTML はテスト専用 fixture であり、モデル生成結果ではない。
- `create_function_app` でサンプルの 6 関数を登録できることを確認。Queue トリガー、ワークフロー orchestrator、tool activity、subagent activity を含む。
- MCR 上の Python / Azurite / DTS イメージ参照の存在を確認。Python と DTS は OCI index digest を固定。
- 非公開 GitHub リポジトリと Codespace を `gh` で作成。Codespace は 4 cores / 16 GB / 32 GB、idle timeout は 30 分。
- Codespace 上でコンテナー構築を完了。Python 3.13.5、Docker 29.8.0、Functions Core Tools 4.14.0、拡張バンドル 4.38.1 を確認。
- Codespace 上でも `14 passed`、Ruff / `pip check` 成功。Azurite / DTS の起動、DTS ダッシュボード HTTP 200、レポート表示サーバー HTTP 200、Functions host `Running` を確認。
- ベースイメージ内の未使用 Yarn apt フィードの署名エラーを除去して再構築成功。署名検証は無効化していない。

## 実モデルでの通し確認（2026-09-12）

Codespace で Azure CLI による本人認証を完了し、指定された Microsoft Foundry の既存デプロイを使って、通常のデモ経路を 2 回実行した。

```bash
./demo start
# 別のターミナルで、各回の完了を待って実行
./demo submit --wait --timeout 600
./demo submit --wait --timeout 600
```

**2 回とも成功。推論は実モデル、PR の状態・履歴は模擬データ。** 実行時のコードは `6dfaf4bb67998c4bb7380952201361fbbd8842fb`。

| 確認項目 | 結果 |
| --- | --- |
| Queue からの起動 | 2 件の異なるメッセージがワークフローを起動 |
| モデルによる計画 | 3 件の独立した PR analyst → 全分析結果を待つ report writer → publisher の依存関係を、両回の `start_workflow` 呼び出しで確認 |
| 並列分析 | 1 回目は 3 activity が同じミリ秒に開始。2 回目は開始時刻の差が 1 ms |
| ワークフロー完了 | 両回とも orchestrator の状態が `Completed` |
| 日本語 HTML | 全 3 件の PR URL と模擬データの明記を確認。`script` 要素なし |
| Blob の更新 | ETag が `0x2308D083F09C4A0` から `0x21AD18584EE6520` に変更 |
| 同じ保存先 | `workflow-reports` 内の Blob は `reports/functions-pr-status.html` の 1 個のみ |
| 表示用ファイル | 最終 Blob の内容と `.demo/reports/report.html` が一致。18,632 bytes |

完了時刻、ワークフロー ID、依存関係、ETag、生成 HTML の SHA-256 は [検証証跡 JSON](e2e/2026-09-12.json) に記録した。時刻は JSON 内では UTC。

今回の実モデル検証では `./demo submit --wait` を使用した。別環境で動作する `./demo verify` コマンド自体の実モデル検証は未実施。

## エージェント定義の日本語化（2026-09-12）

- 3 つの `.agent.md` をランタイムの厳密な設定読み込みで検証し、すべて正常に読み込めた。
- 翻訳前後で、名前・説明・呼び出し条件を除いた設定値と、本文中のコード表記の識別子が一致することを確認した。
- `create_function_app` で 6 関数を登録できることを確認。ワークフロー orchestrator、subagent / tool activity、および元の Queue 名・接続設定を持つ Queue トリガーを含む。
- 上記の実モデル E2E は日本語化前のコードでの結果。日本語化後の実モデル E2E は未実施。

## 未実施

- 実モデル処理中の Functions ワーカー再起動からの継続。

通常の通し実行の成功は、エミュレーターや Codespace の停止後の復元を保証するものではない。
