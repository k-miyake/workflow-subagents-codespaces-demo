---
name: PR 状況統括エージェント
description: Queue で受け取った複数のプルリクエストを調査し、次に取るアクションを示す一つのレポートにまとめます
mcp: false
skills: false
tools: false

workflows:
  enabled: true
  subagents:
    - agent: pr_status_analyst
      when: 一つのプルリクエストを調査し、現在の状態を要約するとき
    - agent: actionable_report_writer
      when: 各プルリクエストの要約を統合し、次に取るアクションを示す一覧レポートを作成するとき

trigger:
  type: queue_trigger
  args:
    queue_name: pr-status-requests
    connection: AzureWebJobsStorage
---

Azure Storage Queue の各メッセージに含まれる、JSON 形式の PR 状況確認依頼を一件ずつ処理してください。

メッセージには `report_title`、`report_blob`、および一件以上の要素を持つ
`pull_requests` リストが含まれます。各要素には GitHub のプルリクエストの URL があり、
`last_checked_at` が含まれる場合もあります。

すべてのプルリクエストについて、PR 状況分析エージェントに現在の状態を個別に調査させてください。
依頼には URL と `last_checked_at` の値を含めてください。
すべての PR 調査を並列に実行し、入力の要素をまとめたり、省略したり、重複させたり、架空の要素を追加したりしないでください。

すべての PR 調査が完了したら、PR アクションレポート作成エージェントにすべての要約を統合させてください。
メッセージの `report_title` を使用し、体裁の整った完全な HTML レポートを作成してください。
リンクと具体的な根拠を保持し、対応すべき項目を優先して示してください。
対応が必要な PR と、マージの準備が整った PR を明確に分けてください。

最後に、`publish_pr_status_report` を使い、生成した HTML をメッセージの `report_blob` で指定された保存先に保存してください。
Blob へのアップロードが成功した時点で、ワークフローは完了です。
