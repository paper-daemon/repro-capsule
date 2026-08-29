# Repro Capsule

「昨日は動いたのに今日動かない」を追うために、**OS / Python / CLIツール / Git状態 / 依存manifest / 環境変数の存在**を1つの再現カプセルに保存する無料OSSです。

```bash
python repro_capsule.py capture /path/to/repo
python repro_capsule.py compare before.json after.json
```

- token / secret / password / API key系の環境変数は常に伏せ字
- デフォルトでは通常の環境変数も値を保存せず「存在」だけ記録
- Git branch / HEAD / dirty状態を保存
- pyproject / requirements / package lock / Dockerfile等をSHA256で固定
- HTML + JSON レポート
- Python 3.10+ / 外部依存なし / MIT

OSS: https://github.com/paper-daemon/repro-capsule
作者サイト: https://paper-daemon.github.io/
