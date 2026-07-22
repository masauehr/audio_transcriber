# 音声文字起こしツール マニュアル

音声ファイルをローカルで文字起こしするCLIツール。faster-whisper（OpenAI Whisperの高速再実装）を使用し、音声データを外部に送信せずすべてローカルで処理する。

---

## ファイルの場所

| ファイル | 説明 |
|---------|------|
| `/Users/masahiro/projects/audio_transcriber/transcribe.py` | メインスクリプト（実行ファイル） |
| `/Users/masahiro/projects/audio_transcriber/requirements.txt` | 依存パッケージ（faster-whisper） |
| `/Users/masahiro/projects/audio_transcriber/input/` | 文字起こし対象の音声ファイル置き場（gitignore対象） |
| `/Users/masahiro/projects/audio_transcriber/output/` | 文字起こし結果テキスト出力先（gitignore対象） |

GitHub: 未公開（音声データ・文字起こし結果を扱うため`input/`・`output/`はコミットしない設計。リポジトリ自体を公開するかは今後判断）

---

## セットアップ

```bash
cd /Users/masahiro/projects/audio_transcriber
pip install -r requirements.txt
```

初回実行時にWhisperモデル（`small` はおよそ500MB）が自動ダウンロードされ、`~/.cache/huggingface/` にキャッシュされる。

対応フォーマット（m4a, mp3, wav, mp4等）の変換にffmpegを使用するため、未インストールの場合は `brew install ffmpeg` が必要。

---

## 実行手順

```bash
cd /Users/masahiro/projects/audio_transcriber
python transcribe.py input/sample.m4a
```

実行後、`output/sample.txt` にタイムスタンプ付きの文字起こし結果が保存される。

### オプション

| オプション | 説明 | デフォルト |
|---|---|---|
| `--model` | Whisperモデルサイズ（tiny/base/small/medium/large-v3） | `small` |
| `--language` | 音声の言語コード（例: `ja`） | 自動検出 |
| `--output` | 出力先テキストファイルパス | `output/<入力ファイル名>.txt` |

```bash
python transcribe.py input/meeting.m4a --model medium --language ja
```

長時間音声（1時間超）を `medium` 以上のモデルでCPU処理するとかなり時間がかかるため、まず `small` で試すことを推奨。

---

## 個人情報の取り扱い

- `input/`（音声ファイル）・`output/`（文字起こし結果）はいずれも個人情報を含み得るため `.gitignore` で除外し、リポジトリにコミットしない
- 文字起こし処理はfaster-whisperによる完全ローカル処理で、音声データは外部（クラウドAPI等）に送信されない

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-07-22 | 新規作成。faster-whisperによるローカルCLIツールとして構築 |
