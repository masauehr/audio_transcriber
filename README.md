# 音声文字起こしツール

詳しくは [MANUAL.md](MANUAL.md) を参照。

音声ファイルをローカルで文字起こしするCLIツール。[faster-whisper](https://github.com/SYSTRAN/faster-whisper)（OpenAI Whisperの高速再実装）を使用し、音声データを外部に送信せず、すべてローカルで処理する。

## 特徴

- **完全ローカル処理**: 音声データはネットワークに送信されない（個人情報を含む音声でも安心して使える）
- **日本語対応**: 言語自動検出、または `--language ja` で明示指定可能
- **タイムスタンプ付き出力**: `[HH:MM:SS - HH:MM:SS] テキスト` 形式でセグメントごとに出力

## セットアップ

```bash
cd audio_transcriber
pip install -r requirements.txt
```

初回実行時にWhisperモデル（`small` はおよそ500MB）が自動ダウンロードされ、`~/.cache/huggingface/` にキャッシュされる。

## 使い方

```bash
# input/ に音声ファイルを置いて実行（出力は output/ 以下に自動生成）
python transcribe.py input/sample.m4a

# モデルサイズ・言語を指定
python transcribe.py input/sample.m4a --model medium --language ja

# 出力先を指定
python transcribe.py input/sample.m4a --output output/result.txt

# オプション例の一覧を表示
python transcribe.py ?
```

### 対応フォーマット

m4a, mp3, wav, mp4 など、ffmpegが対応する主要な音声・動画フォーマット。ffmpeg未インストールの場合は `brew install ffmpeg` が必要。

### モデルサイズ

日本語の会議・スピーチ音声では `small` はやや誤認識が多く、`medium` 以上で実用精度になる体感。詳しい比較・保存先・削除方法は [MANUAL.md](MANUAL.md) を参照。

| モデル | 精度 | 速度（CPU） | 用途 |
|---|---|---|---|
| `tiny` / `base` | 低 | 速い | 下書き・雑音の少ない音声 |
| `small`（デフォルト） | 中 | 標準 | 手早く内容を把握したい場合 |
| `medium` | 高 | やや遅い | 通常の会議・インタビュー |
| `large-v3-turbo` | 高〜最高 | `medium`よりやや遅い程度 | 精度と速度のバランス重視。実用上の第一候補 |
| `large-v3` | 最高 | かなり遅い | 専門用語・多言語混在音声 |

## 注意事項

- `input/` `output/` 配下のファイルは `.gitignore` で除外している（音声データ・文字起こし結果には個人情報が含まれ得るため、リポジトリにはコミットしない）
- 長時間の音声（1時間超）は `medium` 以上のモデルだとCPUでかなり時間がかかる。まず `small` で試すことを推奨
