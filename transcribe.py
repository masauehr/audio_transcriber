"""
音声ファイルから文字起こしを行うCLIツール。

faster-whisper（ローカル実行）を使用し、音声データを外部に送信せずに文字起こしする。

使い方:
    python transcribe.py input/sample.m4a
    python transcribe.py input/sample.m4a --model medium --language ja
    python transcribe.py input/sample.m4a --output output/result.txt
"""

import argparse
import pathlib
import sys

from faster_whisper import WhisperModel


def format_timestamp(seconds: float) -> str:
    """秒数を HH:MM:SS 形式に変換する"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def transcribe(audio_path: pathlib.Path, model_size: str, language: str | None) -> list[str]:
    print(f"モデル読み込み中: {model_size}")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"文字起こし中: {audio_path.name}")
    segments, info = model.transcribe(str(audio_path), language=language, beam_size=5)

    print(f"検出言語: {info.language}（確度 {info.language_probability:.2f}）")

    lines = []
    for segment in segments:
        start = format_timestamp(segment.start)
        end = format_timestamp(segment.end)
        text = segment.text.strip()
        line = f"[{start} - {end}] {text}"
        print(line)
        lines.append(line)

    return lines


def main():
    parser = argparse.ArgumentParser(description="音声ファイルから文字起こしを行う")
    parser.add_argument("audio_file", help="文字起こし対象の音声ファイルパス")
    parser.add_argument(
        "--model",
        default="small",
        help="Whisperモデルサイズ（tiny/base/small/medium/large-v3）。デフォルト: small",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="音声の言語コード（例: ja, en）。省略時は自動検出",
    )
    parser.add_argument("--output", default=None, help="出力先テキストファイルパス")
    args = parser.parse_args()

    audio_path = pathlib.Path(args.audio_file)
    if not audio_path.exists():
        print(f"エラー: 音声ファイルが見つかりません: {audio_path}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = pathlib.Path(args.output)
    else:
        output_path = pathlib.Path("output") / f"{audio_path.stem}.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = transcribe(audio_path, args.model, args.language)

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n文字起こし結果を保存しました: {output_path}")


if __name__ == "__main__":
    main()
