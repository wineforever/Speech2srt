import os
import tempfile
import unittest
from unittest.mock import patch

from speech2srt.application import transcribe_file
from speech2srt.config import SETTINGS


class ApplicationTests(unittest.TestCase):
    def test_orchestrates_one_transcription(self):
        progress = []
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "voice.wav")
            output_dir = os.path.join(temp_dir, "outputs")
            with open(input_path, "wb") as handle:
                handle.write(b"test")

            previous_output = SETTINGS.output_dir
            SETTINGS.output_dir = output_dir
            try:
                with (
                    patch("speech2srt.application.validate_audio", return_value=2.5),
                    patch(
                        "speech2srt.application.transcribe_audio_chunked",
                        return_value={"segments": []},
                    ) as transcribe,
                    patch(
                        "speech2srt.application.generate_subtitles",
                        return_value={
                            "srt": os.path.join(output_dir, "voice.srt"),
                            "txt": os.path.join(output_dir, "voice.txt"),
                        },
                    ),
                ):
                    result = transcribe_file(
                        input_path,
                        asr_engine="bcut",
                        progress_cb=lambda value, message: progress.append((value, message)),
                    )
            finally:
                SETTINGS.output_dir = previous_output

        self.assertEqual(result.duration_seconds, 2.5)
        self.assertEqual(result.engine, "bcut")
        self.assertEqual([value for value, _ in progress], [5, 10, 90, 100])
        transcribe.assert_called_once()

    def test_missing_input_is_explicit(self):
        with self.assertRaises(FileNotFoundError):
            transcribe_file("definitely-missing.wav")


if __name__ == "__main__":
    unittest.main()
