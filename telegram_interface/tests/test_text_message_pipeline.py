# from django.test import TestCase
# from unittest.mock import patch, MagicMock, call
# import telegram_interface.utils

# class ProcessTelegramVoiceTest(TestCase):

#     @patch("telegram_interface.utils.log_point_to_db")
#     @patch("telegram_interface.utils.send_text_message")
#     @patch("telegram_interface.utils.get_language_langid")
#     @patch("telegram_interface.utils.translate_language")
#     @patch("telegram_interface.utils.langchain_agent.utils.run_llm_pipeline")
#     def test_process_telegram_text_message_success(self, mock_run_llm, mock_translate, mock_detect_lang, mock_send_text_message, mock_point):
#         # Arrange
#         mock_detect_lang.return_value = 'hi'
#         mock_translate.side_effect = ["translated to english", "translated back"]
#         mock_run_llm.return_value = "This is the LLM response " * 50

#         body = {
#             "message": {
#                 "chat": {"id": 12345},
#                 "message_id": 67890,
#                 "text": "Some Hindi text message",
#             }
#         }
#         memory = {}
#         chat_id = body["message"]["chat"]["id"]


#         # Act
#         result = telegram_interface.utils.process_telegram_message(body, memory)

#         # Assert
#         self.assertTrue(result)
#         mock_run_llm.assert_called_once()
#         mock_send_text_message.assert_called_once()
#         assert mock_translate.call_count == 2


#     @patch("telegram_interface.utils.log_point_to_db")
#     @patch("telegram_interface.utils.send_text_message")
#     @patch("telegram_interface.utils.get_language_langid")
#     @patch("telegram_interface.utils.translate_language")
#     @patch("telegram_interface.utils.langchain_agent.utils.run_llm_pipeline")
#     def test_process_telegram_text_message_unsupported_language(self, mock_run_llm, mock_translate, mock_detect_lang, mock_send_text_message, mock_point):
#         # Arrange
#         mock_detect_lang.return_value = 'te'


#         body = {
#             "message": {
#                 "chat": {"id": 12345},
#                 "message_id": 67890,
#                 "text": "Some Telugu text message",
#             }
#         }
#         memory = {}
#         chat_id = body["message"]["chat"]["id"]


#         # Act
#         result = telegram_interface.utils.process_telegram_message(body, memory)

#         # Assert
#         self.assertTrue(result)
#         mock_run_llm.assert_not_called()
#         mock_send_text_message.assert_called_once_with(chat_id, "Sorry , the bot couldnt get that.This bot currently supports English, Hindi, Kannada, Malayalam, Tamil.")
#         assert mock_translate.assert_not_called


