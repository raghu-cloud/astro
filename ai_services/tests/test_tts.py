# from django.test import TestCase
# from unittest.mock import patch, Mock
# from ai_services.utils.tts_utils import generate_with_sarvam_ai, SarvamTTSAPIException


# class GenerateWithSarvamAITests(TestCase):
#     @patch("ai_services.utils.tts_utils.log_point_to_db")
#     @patch("ai_services.utils.tts_utils.call_sarvam_tts_api")
#     @patch("ai_services.utils.tts_utils.AudioSegment")
#     def test_tts_success(self, mock_audio_segment, mock_api, mock_log):
#         mock_api.return_value = {
#             "audios": ["UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA="]  # base64 of valid silent wav
#         }
#         mock_audio_segment.from_wav.return_value = Mock()
#         mock_audio_segment.from_wav.return_value.export.return_value = None

#         result = generate_with_sarvam_ai(
#             text="Hello, how are you?",
#             speaker="arvind",
#             model_version="bulbul:v1",
#             chat_id="test123",
#             language="english"
#         )
#         self.assertTrue(isinstance(result, str) and result.endswith(".wav"))
#         mock_log.assert_called()

#     @patch("ai_services.utils.tts_utils.log_point_to_db")
#     @patch("ai_services.utils.tts_utils.call_sarvam_tts_api")
#     def test_tts_api_failure(self, mock_api, mock_log):
#         mock_api.side_effect = SarvamTTSAPIException("API failed after retries")

#         result = generate_with_sarvam_ai(
#             text="This should fail.",
#             speaker="arvind",
#             model_version="bulbul:v1",
#             chat_id="failtest",
#             language="english"
#         )
#         self.assertIn("error", result)
#         mock_log.assert_called()

#     @patch("ai_services.utils.tts_utils.log_point_to_db")
#     def test_tts_chunking_error(self, mock_log):
#         with patch("ai_services.utils.tts_utils.split_text_into_chunks", side_effect=ValueError("Chunking error")):
#             result = generate_with_sarvam_ai(
#                 text="bad text",
#                 speaker="arvind",
#                 model_version="bulbul:v1",
#                 chat_id="chunktest",
#                 language="english"
#             )
#             self.assertIn("error", result)
#             mock_log.assert_called()
