# from django.test import TestCase
# from unittest.mock import patch, MagicMock
# from ai_services.utils.language_translation_utils import translate_with_sarvam
# from ai_services.models import AIServiceConfig

# class TranslateWithSarvamTests(TestCase):
#     @patch("ai_services.utils.language_translation_utils.split_text_into_chunks")
#     @patch("ai_services.utils.language_translation_utils.log_point_to_db")
#     @patch("ai_services.utils.language_translation_utils.requests.post")
#     def test_translate_success(self, mock_post, mock_log, mock_chunk):
#         mock_chunk.return_value = ["hello"]
#         mock_response = MagicMock()
#         mock_response.status_code = 200
#         mock_response.json.return_value = {"translated_text": "नमस्ते"}
#         mock_post.return_value = mock_response
#         AIServiceConfig.objects.create(is_active=True, tts_voice="arvind")
#         result = translate_with_sarvam(
#             text="hello",
#             source_language="english",
#             target_language="hindi",
#             model="mayura:v1",
#             phase=1
#         )
#         self.assertEqual(result, "नमस्ते")
#         mock_log.assert_called()  

#     @patch("ai_services.utils.language_translation_utils.split_text_into_chunks")
#     @patch("ai_services.utils.language_translation_utils.log_point_to_db")
#     @patch("ai_services.utils.language_translation_utils.requests.post")
#     def test_translate_api_failure(self, mock_post, mock_log, mock_chunk):
#         mock_chunk.return_value = ["hello"]
#         mock_response = MagicMock()
#         mock_response.status_code = 400
#         mock_post.return_value = mock_response
#         AIServiceConfig.objects.create(is_active=True, tts_voice="arvind")
#         result = translate_with_sarvam(
#             text="hello",
#             source_language="english",
#             target_language="hindi",
#             model="mayura:v1",
#             phase=1
#         )
#         self.assertIsNone(result)
#         mock_log.assert_called()  

#     @patch("ai_services.utils.language_translation_utils.split_text_into_chunks", side_effect=ValueError("Bad chunking"))
#     def test_translate_chunking_error(self, mock_chunk):
#         AIServiceConfig.objects.create(is_active=True, tts_voice="arvind")
#         result = translate_with_sarvam(
#             text="hello",
#             source_language="english",
#             target_language="hindi",
#             model="mayura:v1",
#             phase=1
#         )
#         self.assertIsNone(result)
        
