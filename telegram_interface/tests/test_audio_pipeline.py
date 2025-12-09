# from django.test import TestCase
# from unittest.mock import patch, MagicMock, call
# import telegram_interface.utils

# class ProcessTelegramVoiceTest(TestCase):

#     @patch("telegram_interface.utils.os.remove")
#     @patch("telegram_interface.utils.log_point_to_db")
#     @patch("telegram_interface.utils.send_text_message")
#     @patch("telegram_interface.utils.get_language_langid")
#     @patch("telegram_interface.utils.translate_language")
#     @patch("telegram_interface.utils.call_litellm") 
#     @patch("telegram_interface.utils.langchain_agent.utils.run_llm_pipeline")
#     @patch("telegram_interface.utils.generate_tts")
#     @patch("telegram_interface.utils.send_telegram_audio")
#     def test_process_telegram_message_audio_transcript_success(
#         self, mock_send_audio, mock_generate_tts, mock_run_llm, mock_call_litellm,  
#         mock_translate, mock_detect_lang, mock_send_text_message, mock_point, mock_remove
#     ):
#         # Arrange
#         mock_detect_lang.return_value = 'hi'
#         mock_translate.side_effect = ["translated to english", "translated back", "translated back tts"]
#         mock_run_llm.return_value = "This is a long LLM response that needs summarizing " * 50
#         mock_call_litellm.return_value = ("Summarized response", "openai/gpt-4")
#         mock_generate_tts.return_value = "dummy_audio_file.ogg"
#         mock_send_audio.return_value = True
#         mock_remove.side_effect = lambda path: print(f"Mock deleted: {path}")

#         body = {
#             "message": {
#                 "chat": {"id": 12345},
#                 "message_id": 67890,
#                 "text": "Some Hindi voice message",
#             }
#         }
#         memory = {}
#         chat_id = body["message"]["chat"]["id"]
#         file_id = "abc123"
#         expected_calls = [
#             call(f"telegram_voice_{file_id}_{chat_id}.ogg"),
#             call(f"telegram_voice_{file_id}_{chat_id}.wav"),
#             call(f"{chat_id}_tts_output.wav"),
#         ]

#         # Act
#         result = telegram_interface.utils.process_telegram_message_audio_transcript(body, memory, file_id)

#         # Assert
#         self.assertTrue(result)
#         mock_send_audio.assert_called_once()
#         mock_generate_tts.assert_called_once()
#         mock_run_llm.assert_called_once()
#         mock_call_litellm.assert_called_once()
#         mock_send_text_message.assert_called_once()
#         mock_translate.assert_any_call("Some Hindi voice message", "hindi", "english", 1)
        

#         mock_remove.assert_has_calls(expected_calls, any_order=True)

#         # Optional: check number of deletions
#         assert mock_remove.call_count == 3


#     @patch("telegram_interface.utils.os.remove")
#     @patch("telegram_interface.utils.log_point_to_db")
#     @patch("telegram_interface.utils.send_text_message")
#     @patch("telegram_interface.utils.get_language_langid")
#     @patch("telegram_interface.utils.translate_language")
#     @patch("telegram_interface.utils.call_litellm") 
#     @patch("telegram_interface.utils.langchain_agent.utils.run_llm_pipeline")
#     @patch("telegram_interface.utils.generate_tts")
#     @patch("telegram_interface.utils.send_telegram_audio")
#     def test_process_telegram_message_audio_transcript_unsupported_language(
#         self, mock_send_audio, mock_generate_tts, mock_run_llm, mock_call_litellm,  
#         mock_translate, mock_detect_lang, mock_send_text_message, mock_log, mock_remove
#     ):
#         # Arrange
#         mock_detect_lang.return_value = 'xyz'  # unsupported language
#         body = {
#             "message": {
#                 "chat": {"id": 12346},
#                 "message_id": 67890,
#                 "text": "uncertain_audio_language",
#             }
#         }
#         memory = {}
#         file_id = "abc123"

#         # Act
#         result = telegram_interface.utils.process_telegram_message_audio_transcript(body, memory, file_id)

#         # Assert
#         self.assertTrue(result)
#         mock_send_text_message.assert_called_once_with(12346, "Sorry , i couldnt get that. Can you please try speaking again?This bot currently supports English, Hindi, Kannada, Malayalam, Tamil.")

    
#     @patch("telegram_interface.utils.os.remove")
#     @patch("telegram_interface.utils.log_point_to_db")
#     @patch("telegram_interface.utils.send_text_message")
#     @patch("telegram_interface.utils.get_language_langid")
#     @patch("telegram_interface.utils.translate_language")
#     @patch("telegram_interface.utils.call_litellm") 
#     @patch("telegram_interface.utils.langchain_agent.utils.run_llm_pipeline")
#     @patch("telegram_interface.utils.generate_tts")
#     @patch("telegram_interface.utils.send_telegram_audio")
#     def test_process_telegram_message_audio_transcript_success_no_summary(
#         self, mock_send_audio, mock_generate_tts, mock_run_llm, mock_call_litellm,  
#         mock_translate, mock_detect_lang, mock_send_text_message, mock_point, mock_remove
#     ):
#         # Arrange
#         mock_detect_lang.return_value = 'hi'
#         mock_translate.side_effect = ["translated to english", "translated back", "translated back tts"]
#         mock_run_llm.return_value = "This is a long LLM response that needs summarizing " * 10
#         # mock_call_litellm.return_value = ("Summarized response", "openai/gpt-4")
#         mock_generate_tts.return_value = "dummy_audio_file.ogg"
#         mock_send_audio.return_value = True
#         mock_remove.side_effect = lambda path: print(f"Mock deleted: {path}")

#         body = {
#             "message": {
#                 "chat": {"id": 12345},
#                 "message_id": 67890,
#                 "text": "Some Hindi voice message",
#             }
#         }
#         memory = {}
#         chat_id = body["message"]["chat"]["id"]
#         file_id = "abc123"
#         expected_calls = [
#             call(f"telegram_voice_{file_id}_{chat_id}.ogg"),
#             call(f"telegram_voice_{file_id}_{chat_id}.wav"),
#             call(f"{chat_id}_tts_output.wav"),
#         ]

#         # Act
#         result = telegram_interface.utils.process_telegram_message_audio_transcript(body, memory, file_id)

#         # Assert
#         self.assertTrue(result)
#         mock_send_audio.assert_called_once()
#         mock_generate_tts.assert_called_once()
#         mock_run_llm.assert_called_once()
#         mock_call_litellm.assert_not_called()
#         mock_send_text_message.assert_called_once()
#         mock_translate.assert_any_call("Some Hindi voice message", "hindi", "english", 1)
        

#         mock_remove.assert_has_calls(expected_calls, any_order=True)

#         # Optional: check number of deletions
#         assert mock_remove.call_count == 3
