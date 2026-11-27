# YAPC::Tokyo 2026 タイムテーブル（非公式モバイル版）

https://miyagawa.co/yapc-tokyo-2026/

[公式タイムテーブル (fortee)](https://fortee.jp/yapc-tokyo-2026/timetable) をスマホで見やすくした**非公式**ビューです。
正確な情報は公式を確認してください。

- 日付タブ（前夜祭 / Day 1 / Day 2 / 時間未定）、トラックフィルタ、★（ブラウザに保存）
- JST の現在時刻で「開催中 / 次」をハイライト
- ライト / ダークモード対応、フレームワークなしの静的ページ

## カレンダー (.ics)

- `ics/all.ics` 全日程、`ics/talks.ics` トークのみ、`ics/2026-11-2X.ics` 日別
- `ics/events/<uuid>.ics` トーク単位（各カードの「カレンダーに追加」）
- ★ を付けたトークはページ下部からまとめてダウンロード
- `webcal://miyagawa.co/yapc-tokyo-2026/ics/all.ics` で購読すると更新が反映されます

## データ更新

データは fortee の公開 API `https://fortee.jp/yapc-tokyo-2026/api/timetable` から取得します。

```sh
python3 scripts/fetch.py   # data/timetable.json と ics/ を再生成
git add -A data ics && git commit -m "Refresh timetable" && git push
```

GitHub Actions の `Refresh timetable` ワークフローは手動実行 (workflow_dispatch) と、
会期中（11/28 07:00 – 11/29 19:00 JST）の 1 時間ごとの cron で同じことを行い、変更があればコミットします。
