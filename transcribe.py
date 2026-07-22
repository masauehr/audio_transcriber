"""
音声ファイルから文字起こしを行うCLIツール。

faster-whisper（ローカル実行）を使用し、音声データを外部に送信せずに文字起こしする。
実行するたびに、時刻タグ付きと時刻タグなしの整形済みの2種類のテキストファイルを output/ に生成する。
出力先を明示指定しない場合、ファイル名には実行日時とモデル名を含めるため、同じ音声ファイルを
異なるモデルや複数回実行しても上書きされない（例: sample_medium_20260722_143000.txt）。

使い方:
    python transcribe.py input/sample.m4a
    python transcribe.py input/sample.m4a --model medium --language ja
    python transcribe.py input/sample.m4a --output output/result.txt
"""

import argparse
import datetime
import pathlib
import sys

from faster_whisper import WhisperModel


def format_timestamp(seconds: float) -> str:
    """秒数を HH:MM:SS 形式に変換する"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def transcribe(
    audio_path: pathlib.Path, model_size: str, language: str | None
) -> tuple[list[str], list[str]]:
    print(f"モデル読み込み中: {model_size}")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"文字起こし中: {audio_path.name}")
    segments, info = model.transcribe(str(audio_path), language=language, beam_size=5)

    print(f"検出言語: {info.language}（確度 {info.language_probability:.2f}）")

    timestamped_lines = []
    texts = []
    for segment in segments:
        start = format_timestamp(segment.start)
        end = format_timestamp(segment.end)
        text = segment.text.strip()
        line = f"[{start} - {end}] {text}"
        print(line)
        timestamped_lines.append(line)
        texts.append(text)

    return timestamped_lines, texts


def format_plain_text(texts: list[str]) -> str:
    """セグメントのテキストを結合し、時刻タグなし・句点区切りの読みやすい形に整形する"""
    full_text = "".join(texts)
    sentences = [s for s in full_text.split("。") if s.strip()]
    return "\n".join(f"{s}。" for s in sentences)


USAGE_EXAMPLES = """\
使い方の例:

  基本（モデル small・言語自動検出）
    python transcribe.py input/sample.m4a
    → output/sample_small_<実行日時>.txt（時刻タグ付き）と
      output/sample_small_<実行日時>_formatted.txt（整形済み）を生成
      ※ 実行のたびに日時が変わるので上書きされない

  モデルサイズと言語を指定
    python transcribe.py input/sample.m4a --model medium --language ja

  高精度モデルで実行（速度と精度のバランス重視）
    python transcribe.py input/sample.m4a --model large-v3-turbo --language ja

  最高精度モデルで実行（CPUではかなり時間がかかる）
    python transcribe.py input/sample.m4a --model large-v3 --language ja

  出力先を指定（この場合はファイル名そのまま・上書きされるので注意）
    python transcribe.py input/sample.m4a --output output/result.txt

モデルサイズの選び方・容量・削除方法は MANUAL.md を参照。
"""


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "?":
        print(USAGE_EXAMPLES)
        sys.exit(0)

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
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = pathlib.Path("output") / f"{audio_path.stem}_{args.model}_{timestamp}.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamped_lines, texts = transcribe(audio_path, args.model, args.language)

    output_path.write_text("\n".join(timestamped_lines), encoding="utf-8")
    print(f"\n文字起こし結果（時刻タグ付き）を保存しました: {output_path}")

    formatted_path = output_path.with_name(f"{output_path.stem}_formatted.txt")
    formatted_path.write_text(format_plain_text(texts), encoding="utf-8")
    print(f"整形済みテキスト（時刻タグなし）を保存しました: {formatted_path}")


if __name__ == "__main__":
    main()
