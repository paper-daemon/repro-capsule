# Repro Capsule

「昨日は動いたのに今日動かない」を追うために、**OS / Python / CLIツール / Git状態 / 依存manifest / 環境変数の存在**を1つの再現カプセルに保存する無料OSSです。

```bash
python repro_capsule.py capture /path/to/repo
python repro_capsule.py compare before.json after.json
```

- token / secret / password / API key系の環境変数は常に伏せ字
- `--include-env-values` 使用時も、`user:password@host` を含むURLや `token` / `secret` 等のquery parameterを持つURLは常に伏せ字
  - hostを持たない `sqlite:///...?...` / `file:///...?...` 等でも、secret query keyがあれば伏せ字
  - `sig` / `signature` / `X-Amz-Signature` / `X-Goog-Signature` を含むsigned URLも伏せ字
- credentialを含まない通常の公開URLは `--include-env-values` 使用時に値を記録できます
- デフォルトでは通常の環境変数も値を保存せず「存在」だけ記録
- Git branch / HEAD / dirty状態を保存
- pyproject / requirements / package lock / Dockerfile等をSHA256で固定
- HTML + JSON レポート
- Python 3.10+ / 外部依存なし / MIT

回帰確認:

```bash
python3 -m unittest -v tests.test_repro_capsule
```

OSS: https://github.com/paper-daemon/repro-capsule
作者サイト: https://paper-daemon.github.io/

## BOOTH
0円配布: https://amase-memo.booth.pm/items/8778562

## Git snapshot boundary
- capture時に指定したJSON/HTML出力はgit dirty判定から除外し、ツール自身の出力で次回captureがdirtyになる自己汚染を防ぎます。

## Project root boundary

`capture` は存在するディレクトリだけを対象にします。存在しないpathや通常ファイルをproject rootとして渡した場合は、空のcapsuleを正常生成せず、出力ファイルを書く前にエラー終了します。
