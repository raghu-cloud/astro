# from django.test import TestCase

# # Create your tests here.
# from unittest.mock import patch, MagicMock
# from ai_services.utils.stt_utils import generate_with_sarvam_ai


# class GenerateWithSarvamAiTests(TestCase):
#     @patch("ai_services.utils.stt_utils.log_point_to_db")
#     @patch("ai_services.utils.stt_utils.get_audio_duration")
#     @patch("ai_services.utils.stt_utils.requests.post")
#     def test_generate_with_sarvam_ai_success(self, mock_post, mock_duration, mock_log):
#         mock_duration.return_value = 5.6  # seconds

#         # Simulate successful API response
#         mock_response = MagicMock()
#         mock_response.status_code = 200
#         mock_response.json.return_value = {
#             "transcript": "मेरी शादी नहीं हो रही, मुझे क्या करना चाहिए?",
#             "language_code": "hi-IN"
#         }
#         mock_post.return_value = mock_response



#         result = generate_with_sarvam_ai("voice_samples/mere_shaaadi_nahi_hori.ogg", "saarika:v2")

#         self.assertEqual(result, "मेरी शादी नहीं हो रही, मुझे क्या करना चाहिए?")
#         mock_post.assert_called_once()
#         mock_log.assert_called()  # You can also assert call args if needed


#     @patch("ai_services.utils.stt_utils.log_point_to_db")
#     @patch("ai_services.utils.stt_utils.get_audio_duration")
#     @patch("ai_services.utils.stt_utils.requests.post")
#     def test_generate_with_sarvam_ai_uncertain_language(self, mock_post, mock_duration, mock_log):
#         mock_duration.return_value = 5.6

#         # Simulate valid response with unsupported language
#         mock_response = MagicMock()
#         mock_response.status_code = 200
#         mock_response.json.return_value = {
#             "transcript": "some telugu transcript",
#             "language_code": "te-IN"  # Unsupported language
#         }
#         mock_post.return_value = mock_response

#         result = generate_with_sarvam_ai("voice_samples/mere_shaaadi_nahi_hori.ogg", "saarika:v2")

#         self.assertEqual(result, "uncertain_audio_language")
#         mock_post.assert_called_once()
#         mock_log.assert_called()


#     @patch("ai_services.utils.stt_utils.log_point_to_db")
#     @patch("ai_services.utils.stt_utils.get_audio_duration")
#     @patch("ai_services.utils.stt_utils.requests.post")
#     def test_generate_with_sarvam_ai_api_failure(self, mock_post, mock_duration, mock_log):
#         mock_duration.return_value = 5.6

#         # Simulate failure (e.g. 400 Bad Request)
#         mock_response = MagicMock()
#         mock_response.status_code = 400
#         mock_post.return_value = mock_response

#         result = generate_with_sarvam_ai("voice_samples/mere_shaaadi_nahi_hori.ogg", "saarika:v2")
#         self.assertEqual(result, "uncertain_audio_language")
#         self.assertEqual(mock_post.call_count, 2)  # because 1 retry



            

