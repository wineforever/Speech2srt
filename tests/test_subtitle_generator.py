import tempfile
import unittest
from pathlib import Path

from speech2srt.config import SETTINGS
from speech2srt.subtitle_generator import generate_subtitles, split_sentences


class SubtitleGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.max_chars = SETTINGS.subtitle_max_chars
        self.min_duration = SETTINGS.subtitle_min_duration

    def tearDown(self):
        SETTINGS.subtitle_max_chars = self.max_chars
        SETTINGS.subtitle_min_duration = self.min_duration

    def test_splits_long_text_and_keeps_monotonic_timestamps(self):
        SETTINGS.subtitle_max_chars = 4
        SETTINGS.subtitle_min_duration = 0.2
        sentences = split_sentences(
            [{"start": 1.0, "end": 3.0, "text": "你好世界。测试字幕！"}]
        )

        self.assertGreaterEqual(len(sentences), 3)
        self.assertTrue(all(item["end"] > item["start"] for item in sentences))
        self.assertTrue(
            all(left["end"] <= right["start"] for left, right in zip(sentences, sentences[1:]))
        )

    def test_generates_utf8_srt_and_txt(self):
        result = {"segments": [{"start": 0, "end": 1.2, "text": "你好。"}]}
        with tempfile.TemporaryDirectory() as temp_dir:
            outputs = generate_subtitles(result, temp_dir, "demo.mp3")
            srt = Path(outputs["srt"]).read_text(encoding="utf-8")
            txt = Path(outputs["txt"]).read_text(encoding="utf-8")

        self.assertIn("00:00:00,000 --> 00:00:01,200", srt)
        self.assertEqual(txt, "你好。\n")


if __name__ == "__main__":
    unittest.main()
