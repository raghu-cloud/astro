from django.test import TestCase
from django.test import TestCase
from unittest.mock import patch, MagicMock, AsyncMock
import unittest
from langchain_agent.models import User, store_detail
from unittest.mock import call
from langchain_agent.utils import (
    build_state_graph,
    run_llm_pipeline,
    intent_node,
    kundli_node,
    horoscope_node,
    store_in_db_node,
    q_and_a_kundli_node,
)

from langchain_agent.pdf_utils.generate_pdf import call_divine, call_horoscope
from django.db import connection
from django.db.utils import OperationalError
from unittest.mock import AsyncMock, patch, ANY


def ensure_connection():
    try:
        connection.ensure_connection()
    except OperationalError:
        connection.connect()


class Test(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            id=1,
            daily_horoscope_flow=False,
            weekly_horoscope_flow=False,
            kundli_flow=False,
        )
        self.store_detail = store_detail.objects.create(
            message_text="Hi",
            metric="user_message",
            message_type="text",
            user_id=self.user.id,
            message_id=1,
        )

    # @patch("langchain_agent.utils.log_point_to_db")
    # @patch("telegram_interface.utils.send_text_message")
    # @patch("telegram_interface.utils.send_telegram_document")
    # def test_build_state_graph_basic_input(self, mock_send_doc, mock_send_text,mock_log_point):

    #     user_message = "hi"
    #     chat_id = self.user.id
    #     message_id = 1
    #     user_message_type = "text"
    #     mock_send_doc.return_value = {"ok": True, "result": {"message_id": 123}}
    #     mock_send_text.return_value = None

    #     # Act
    #     result = run_llm_pipeline(
    #         user_message, "sdf", "sdf", chat_id, message_id, user_message_type
    #     )
    #     mock_log_point.assert_called()

        # Assert
   
    # @patch("langchain_agent.utils.os.remove")

    # @patch("langchain_agent.pdf_utils.generate_pdf.s3.upload_file")   
    # @patch(
    #     "langchain_agent.pdf_utils.generate_pdf.store_kundli_in_db",
    #     new_callable=AsyncMock,
    # )
    # @patch(
    #     "langchain_agent.pdf_utils.generate_pdf.store_key_value_pair_kundli_in_db",
    #     new_callable=AsyncMock,
    # )
    # @patch("langchain_agent.pdf_utils.generate_pdf.main", new_callable=AsyncMock)
    # @patch(
    #     "langchain_agent.pdf_utils.generate_pdf.generate_mobile_friendly_kundli",
    #     new_callable=AsyncMock,
    # )    
    # @patch("langchain_agent.utils.log_point_to_db")
    # @patch("telegram_interface.utils.send_text_message")
    # @patch("telegram_interface.utils.send_telegram_document")
    # def test_build_state_graph_kundli_input(self, mock_send_doc, mock_send_text,mock_log_point, mock_generate,
    #     mock_main,
    #     mock_store_key_value,
    #     mock_store_kundli,mock_upload_file,mock_remove):

    #     user_message = "where is kundli? name raghu bangalore 11 am male 25-09-2001"
    #     chat_id = self.user.id
    #     message_id = 1
    #     mock_main.return_value = "data"
    #     user_message_type = "text"
    #     mock_send_doc.return_value = {"ok": True, "result": {"message_id": 123}}
    #     mock_send_text.return_value = None
    #     output_path='1_kundli.pdf'

    #     # Act
    #     result = run_llm_pipeline(
    #         user_message, "sdf", "sdf", chat_id, message_id, user_message_type
    #     )
    #     # Assert
    #     mock_send_doc.assert_called_once_with(chat_id, f"{chat_id}_kundli.pdf")
    #     mock_send_text.assert_called_once_with(
    #         chat_id,
    #         f"We are generating your personalised Kundli, Please wait for a minute or two....",
    #     )
    #     mock_log_point.assert_called()
    #     mock_store_kundli.assert_awaited_once_with("data", chat_id)
    #     mock_store_key_value.assert_awaited_once_with("data", chat_id)
    #     mock_generate.assert_awaited_once_with("data", chat_id, output_path=output_path)
    #     mock_upload_file.assert_called_once_with(
    #     "1_kundli.pdf",
    #     "astro-ai",
    #     "1_kundli.pdf",
    #     ExtraArgs={"ACL": "public-read", "ContentType": "application/pdf"},
    # )
    #       # Assert os.remove was called with the correct file
    #     mock_remove.assert_called_once_with(f"{chat_id}_kundli.pdf")


    
    @patch("langchain_agent.pdf_utils.generate_pdf.requests.post")
    @patch("langchain_agent.utils.log_point_to_db")
    def test_build_state_graph_horoscope_input(self,mock_log_point,mock_post):

        user_message = "give me my horoscope? name raghu bangalore 11 am male 25-09-2001"
        chat_id = self.user.id
        message_id = 1
        user_message_type = "text"
        mock_response_roxy = MagicMock()
        mock_response_roxy.status_code = 200
        mock_response_roxy.json.return_value = {
            "name": "Raghu",
            "zodiac_sign": "Libra",
            "personality": "Diplomatic, charming, and harmonious...",
            "symbol": "♎",
            "element": "Air",
            "modality": "Cardinal",
            "image": "https://cdn.roxyapi.com/img/astrology/libra.png",
        }

        mock_response_divine = MagicMock()
        mock_response_divine.status_code = 200
        mock_response_divine.json.return_value = {'success': 1, 'data': {'sign': 'Libra', 'prediction': {'personal': 'In your personal relationships, communication is key to understanding and bonding more deeply with loved ones. Listen actively and express your feelings honestly. A heart-to-heart conversation might be on the cards, leading to greater clarity and emotional satisfaction. Maintain balance in give and take, ensuring that both parties feel valued. Social gatherings could introduce you to interesting personalities, broadening your social circle.', 'health': 'Pay attention to your physical well-being today. Incorporating light exercise or mindfulness practices can significantly enhance your energy levels and mental clarity. Be mindful of your diet, as overindulgence may throw your digestive system off balance. Ensure you get sufficient rest, allowing your body and mind to rejuvenate. Staying hydrated and incorporating stress-busting activities like yoga can have positive effects on your overall wellness.', 'profession': "Today, focus on nurturing collaborations and partnerships at work. Your diplomatic skills can smooth out potential conflicts and foster teamwork. An opportunity for a new project or role may arise, and it's important to weigh the pros and cons carefully. Keep an open mind and trust your instincts when making decisions. By recognizing others’ contributions, you can enhance your own position and garner respect from peers.", 'emotions': 'Emotionally, you might find yourself reflective, pondering past experiences and their impact on your present life. This introspection can offer valuable insights and help release any lingering emotional blockages. Allow yourself to feel and process these emotions without judgment. Seek comfort in creative or artistic pursuits that resonate with your current emotional state, offering a healthy outlet for self-expression.', 'travel': 'Today could bring unexpected travel opportunities, providing a chance to explore new environments. Whether for work or leisure, remain adaptable and open to new experiences. Make sure to plan ahead to minimize any stress and maximize enjoyment. A day trip or spontaneous outing might offer a refreshing change of scenery and new perspectives, bringing excitement and novelty into your routine.', 'luck': ['Colors of the day : Blue, Pink', 'Lucky Numbers of the day : 3, 9, 14', 'Lucky Alphabets you will be in sync with : L, B', 'Cosmic Tip : Embrace spontaneity; unexpected joy comes from surprises.', 'Tips for Singles : Explore new interests to expand your social horizons.', 'Tips for Couples : Plan a surprise date night to rekindle romance.']}, 'special': {'lucky_color_codes': ['#0000FF', '#FFC0CB']}}}

        def post_side_effect(url, *args, **kwargs):

            if "roxyapi.com" in url:
                return mock_response_roxy
            elif "astroapi-5.divineapi.com" in url:
                return mock_response_divine
            else:
                raise ValueError("Unexpected URL in test")

        mock_post.side_effect = post_side_effect


    
        result = run_llm_pipeline(
            user_message, "fg", "sdf", chat_id, message_id, user_message_type
        )
        # mock_response_roxy = MagicMock()
        # mock_response_roxy.status_code = 200
        # mock_response_roxy.json.return_value = {
        #     "name": "Raghu",
        #     "zodiac_sign": "Libra",
        #     "personality": "Diplomatic, charming, and harmonious...",
        #     "symbol": "♎",
        #     "element": "Air",
        #     "modality": "Cardinal",
        #     "image": "https://cdn.roxyapi.com/img/astrology/libra.png",
        # }

        # mock_response_divine = MagicMock()
        # mock_response_divine.status_code = 200
        # mock_response_divine.json.return_value = {'success': 1, 'data': {'sign': 'Libra', 'prediction': {'personal': 'In your personal relationships, communication is key to understanding and bonding more deeply with loved ones. Listen actively and express your feelings honestly. A heart-to-heart conversation might be on the cards, leading to greater clarity and emotional satisfaction. Maintain balance in give and take, ensuring that both parties feel valued. Social gatherings could introduce you to interesting personalities, broadening your social circle.', 'health': 'Pay attention to your physical well-being today. Incorporating light exercise or mindfulness practices can significantly enhance your energy levels and mental clarity. Be mindful of your diet, as overindulgence may throw your digestive system off balance. Ensure you get sufficient rest, allowing your body and mind to rejuvenate. Staying hydrated and incorporating stress-busting activities like yoga can have positive effects on your overall wellness.', 'profession': "Today, focus on nurturing collaborations and partnerships at work. Your diplomatic skills can smooth out potential conflicts and foster teamwork. An opportunity for a new project or role may arise, and it's important to weigh the pros and cons carefully. Keep an open mind and trust your instincts when making decisions. By recognizing others’ contributions, you can enhance your own position and garner respect from peers.", 'emotions': 'Emotionally, you might find yourself reflective, pondering past experiences and their impact on your present life. This introspection can offer valuable insights and help release any lingering emotional blockages. Allow yourself to feel and process these emotions without judgment. Seek comfort in creative or artistic pursuits that resonate with your current emotional state, offering a healthy outlet for self-expression.', 'travel': 'Today could bring unexpected travel opportunities, providing a chance to explore new environments. Whether for work or leisure, remain adaptable and open to new experiences. Make sure to plan ahead to minimize any stress and maximize enjoyment. A day trip or spontaneous outing might offer a refreshing change of scenery and new perspectives, bringing excitement and novelty into your routine.', 'luck': ['Colors of the day : Blue, Pink', 'Lucky Numbers of the day : 3, 9, 14', 'Lucky Alphabets you will be in sync with : L, B', 'Cosmic Tip : Embrace spontaneity; unexpected joy comes from surprises.', 'Tips for Singles : Explore new interests to expand your social horizons.', 'Tips for Couples : Plan a surprise date night to rekindle romance.']}, 'special': {'lucky_color_codes': ['#0000FF', '#FFC0CB']}}}

        # def post_side_effect(url, *args, **kwargs):

        #     if "roxyapi.com" in url:
        #         return mock_response_roxy
        #     elif "astroapi-5.divineapi.com" in url:
        #         return mock_response_divine
        #     else:
        #         raise ValueError("Unexpected URL in test")

        # mock_post.side_effect = post_side_effect

        mock_log_point.assert_called()

   


    # @patch("langchain_agent.utils.log_point_to_db")
    # def test_build_state_graph_q_and_a_input(self,mock_log_point):

    #     user_message = "tell me about marriage"
    #     chat_id = self.user.id
    #     message_id = 1
    #     user_message_type = "text"

    #     # Act
    #     result = run_llm_pipeline(
    #         user_message, "fg", "sdf", chat_id, message_id, user_message_type
    #     )
    #     mock_log_point.assert_called()

        # #Assert
        # mock_send_doc.assert_called_once_with(chat_id, f"{chat_id}_kundli.pdf")
        # mock_send_text.assert_called_once_with(chat_id, f"We are generating your personalised Kundli, Please wait for a minute or two....")


#     #     #     self.assertEqual(result.get("chat_id"), chat_id)
    @patch("langchain_agent.utils.log_point_to_db")
    @patch("langchain_agent.utils.decision_node")
    def test_run_llm_pipeline_intent_node_path(self, mock_decision_node,mock_log_point):
        # Arrange
        user_message = "Tell me about marriage"
        message_id = 1
        user_message_type = "text"
        chat_id = self.user.id

        # mock_call_litellm.return_value = (
        #     "Your marriage will be happy and successful.",
        #     "gpt-4",
        #     "v1",
        #     32,
        #     0.04
        # )

        mock_decision_node.return_value = "hello"

        # Act
        result = intent_node(user_message, chat_id, message_id, user_message_type)

        # Assert
        self.assertEqual(result, "hello")

        mock_decision_node.assert_called_with(
            chat_id, "conversation", message_id, user_message_type
        )
        # mock_log_point.assert_called()
#         mock_log_point.assert_any_call(
#     health_metric="intent_node",
#     phase="total_time",
#     latency=ANY,
#     success=True
# )

#         mock_log_point.assert_any_call(
#     health_metric="intent_node",
#     phase="llm_time",
#     latency=ANY,
#     model=ANY,
#     tokens=ANY,
#     cost=ANY,
#     model_version=ANY,
#     success=True
# )
#     @patch("langchain_agent.utils.log_point_to_db")
#     @patch("langchain_agent.utils.decision_node")
#     def test_run_llm_pipeline_intent_node_path_kundli(self, mock_decision_node,mock_log_point):
#         # Arrange
#         user_message = "give me my kundli"
#         message_id = 1
#         user_message_type = "text"
#         chat_id = self.user.id

#         # mock_call_litellm.return_value = (
#         #     "Your marriage will be happy and successful.",
#         #     "gpt-4",
#         #     "v1",
#         #     32,
#         #     0.04
#         # )

#         mock_decision_node.return_value = "hello"

#         # Act
#         result = intent_node(user_message, chat_id, message_id, user_message_type)

#         # Assert
#         self.assertEqual(result, "hello")

#         mock_decision_node.assert_called_with(
#             chat_id, "kundli", message_id, user_message_type
#         )
#         mock_log_point.assert_called()
#     @patch("langchain_agent.utils.log_point_to_db")
#     @patch("langchain_agent.utils.decision_node")
#     def test_run_llm_pipeline_intent_node_path_horoscope(self, mock_decision_node,mock_log_point):
#         # Arrange
#         user_message = "give me my horoscope"
#         message_id = 1
#         user_message_type = "text"
#         chat_id = self.user.id

#         # mock_call_litellm.return_value = (
#         #     "Your marriage will be happy and successful.",
#         #     "gpt-4",
#         #     "v1",
#         #     32,
#         #     0.04
#         # )

#         mock_decision_node.return_value = "hello"
#         # Act
#         result = intent_node(user_message, chat_id, message_id, user_message_type)
#         # Assert
#         self.assertEqual(result, "hello")

#         mock_decision_node.assert_called_with(
#             chat_id, "daily horoscope", message_id, user_message_type
#         )
#         mock_log_point.assert_called()

#     @patch("langchain_agent.utils.log_point_to_db")
#     @patch("langchain_agent.utils.decision_node")
#     def test_run_llm_pipeline_intent_node_path_weekly_horoscope(
#         self, mock_decision_node,mock_log_point
#     ):
#         # Arrange
#         user_message = "give me my weekly horoscope"
#         message_id = 1
#         user_message_type = "text"
#         chat_id = self.user.id

#         # mock_call_litellm.return_value = (
#         #     "Your marriage will be happy and successful.",
#         #     "gpt-4",
#         #     "v1",
#         #     32,
#         #     0.04
#         # )

#         mock_decision_node.return_value = "hello"
#         # Act
#         result = intent_node(user_message, chat_id, message_id, user_message_type)
#         # Assert
#         self.assertEqual(result, "hello")

#         mock_decision_node.assert_called_with(
#             chat_id, "weekly horoscope", message_id, user_message_type
#         )
#         mock_log_point.assert_called()
#     @patch("langchain_agent.utils.log_point_to_db")
#     @patch("langchain_agent.utils.call_divine")
#     @patch("telegram_interface.utils.send_text_message")
#     @patch("langchain_agent.utils.store_detail")
#     @patch("langchain_agent.utils.User")
#     def test_run_llm_pipeline_kundli_node_path(
#         self, mock_user_model, mock_store_detail, mock_send_text, mock_divine_api,mock_log_point
#     ):
#         # Arrange
#         chat_id = 123
#         message_id = 1
#         user_message_type = "text"
#         # Mock latest user message
#         mock_user_message_obj = MagicMock()
#         mock_user_message_obj.message_text = (
#             "Give my kundli name:raghu male bangalore 11 am 25-09-2001"
#         )
#         mock_user_query = MagicMock()
#         mock_user_query.latest.return_value = mock_user_message_obj
#         # ----- Mock latest bot message -----
#         mock_bot_message_obj = MagicMock()
#         mock_bot_message_obj.message_text = "This is the latest bot message"
#         mock_bot_query = MagicMock()
#         mock_bot_query.order_by.return_value.first.return_value = mock_bot_message_obj

#         # ----- Patch store_detail.objects.filter to return the right mock -----
#         def filter_side_effect(*args, **kwargs):
#             if kwargs.get("metric") == "user_message":
#                 return mock_user_query
#             elif kwargs.get("metric") == "bot_message":
#                 return mock_bot_query
#             return MagicMock()

#         mock_store_detail.objects.filter.side_effect = filter_side_effect
#         mock_divine_api.return_value = "Kundli PDF generated successfully"
#         # Act
#         result = kundli_node(chat_id, message_id, user_message_type)
#         mock_send_text.assert_called_once_with(
#             chat_id,
#             f"We are generating your personalised Kundli, Please wait for a minute or two....",
#         )
#         # Assert
#         self.assertEqual(result, "Kundli PDF generated successfully")
#         mock_log_point.assert_called()
#     @patch("langchain_agent.utils.log_point_to_db")
#     @patch("langchain_agent.utils.store_in_db_node")
#     @patch("langchain_agent.utils.call_litellm")
#     @patch("langchain_agent.utils.store_detail")
#     @patch("langchain_agent.utils.User")
#     def test_run_llm_pipeline_kundli_node_missing_path(
#         self,
#         mock_user_model,
#         mock_store_detail,
#         mock_call_litellm,
#         mock_store_in_db,
#         mock_log_point
#     ):
#         # Arrange
#         chat_id = 123
#         message_id = 1
#         user_message_type = "text"

#         # Mock latest user message
#         mock_user_message_obj = MagicMock()
#         mock_user_message_obj.message_text = (
#             "Give my horoscope male bangalore 11 am 25-09-2001"
#         )
#         mock_user_query = MagicMock()
#         mock_user_query.latest.return_value = mock_user_message_obj

#         # ----- Mock latest bot message -----
#         mock_bot_message_obj = MagicMock()
#         mock_bot_message_obj.message_text = "This is the latest bot message"
#         mock_bot_query = MagicMock()
#         mock_bot_query.order_by.return_value.first.return_value = mock_bot_message_obj

#         # ----- Patch store_detail.objects.filter to return the right mock -----
#         def filter_side_effect(*args, **kwargs):
#             if kwargs.get("metric") == "user_message":
#                 return mock_user_query
#             elif kwargs.get("metric") == "bot_message":
#                 return mock_bot_query
#             return MagicMock()

#         mock_store_detail.objects.filter.side_effect = filter_side_effect
#         mock_call_litellm.return_value = (
#             "LLM generated response content",  # content
#             "gpt-4",  # model_name
#             "v1",  # model_version
#             100,  # tokens
#             0.02,  # cost
#         )
#         # Act
#         result = kundli_node(chat_id, message_id, user_message_type)
#         mock_store_in_db.assert_called_once_with(
#             chat_id, "LLM generated response content", message_id, user_message_type
#         )
#         mock_log_point.assert_called()
#     @patch("langchain_agent.utils.log_point_to_db")
#     @patch("langchain_agent.utils.store_in_db_node")
#     @patch("langchain_agent.utils.call_litellm")
#     @patch("langchain_agent.utils.store_detail")
#     @patch("langchain_agent.utils.User")
#     def test_run_llm_pipeline_horoscope_node(
#         self,
#         mock_user_model,
#         mock_store_detail,
#         mock_call_litellm,
#         mock_store_in_db,
#         mock_log_point,
#     ):
#         chat_id = 123
#         message_id = 1
#         user_message_type = "text"

#         # Mock latest user message
#         mock_user_message_obj = MagicMock()
#         mock_user_message_obj.message_text = (
#             "Give my horoscope male bangalore 11 am 25-09-2001"
#         )
#         mock_user_query = MagicMock()
#         mock_user_query.latest.return_value = mock_user_message_obj

#         # ----- Mock latest bot message -----
#         mock_bot_message_obj = MagicMock()
#         mock_bot_message_obj.message_text = "This is the latest bot message"
#         mock_bot_query = MagicMock()
#         mock_bot_query.order_by.return_value.first.return_value = mock_bot_message_obj

#         # ----- Patch store_detail.objects.filter to return the right mock -----
#         def filter_side_effect(*args, **kwargs):

#             if kwargs.get("metric") == "user_message":
#                 return mock_user_query
#             elif kwargs.get("metric") == "bot_message":
#                 return mock_bot_query
#             return MagicMock()

#         mock_store_detail.objects.filter.side_effect = filter_side_effect
#         mock_call_litellm.return_value = (
#             "LLM generated response content",  # content
#             "gpt-4",  # model_name
#             "v1",  # model_version
#             100,  # tokens
#             0.02,  # cost
#         )

#         # Act
#         result = horoscope_node(
#             chat_id, "daily horoscope", message_id, user_message_type
#         )
#         mock_store_in_db.assert_called_once_with(
#             chat_id, "LLM generated response content", message_id, user_message_type
#         )
#         mock_log_point.assert_called()

#     @patch("langchain_agent.utils.log_point_to_db")
#     @patch("langchain_agent.utils.call_horoscope")
#     @patch("langchain_agent.utils.store_detail")
#     @patch("langchain_agent.utils.User")
#     def test_run_llm_pipeline_horoscope_node_missing_path(
#         self,mock_user_model, mock_store_detail, mock_call_horoscope,mock_log_point
#     ):
#         chat_id = 123
#         message_id = 1
#         user_message_type = "text"

#         # Mock latest user message
#         mock_user_message_obj = MagicMock()
#         mock_user_message_obj.message_text = (
#             "Give my horoscope male Raghu bangalore 11 am 25-09-2001"
#         )
#         mock_user_query = MagicMock()
#         mock_user_query.latest.return_value = mock_user_message_obj

#         # ----- Mock latest bot message -----
#         mock_bot_message_obj = MagicMock()
#         mock_bot_message_obj.message_text = "This is the latest bot message"
#         mock_bot_query = MagicMock()
#         mock_bot_query.order_by.return_value.first.return_value = mock_bot_message_obj

#         # ----- Patch store_detail.objects.filter to return the right mock -----
#         def filter_side_effect(*args, **kwargs):
#             if kwargs.get("metric") == "user_message":
#                 return mock_user_query
#             elif kwargs.get("metric") == "bot_message":
#                 return mock_bot_query
#             return MagicMock()

#         mock_store_detail.objects.filter.side_effect = filter_side_effect

#         # Act
#         result = horoscope_node(
#             chat_id, "daily horoscope", message_id, user_message_type
#         )
#         mock_call_horoscope.assert_called_once_with(
#             {"name": "Raghu", "time": "11:00:00", "dob": "2001-09-25"},
#             chat_id,
#             "daily horoscope",
#             message_id,
#             user_message_type,
#         )
#         mock_log_point.assert_called()

    
#     @patch("langchain_agent.utils.log_point_to_db")
#     @patch("langchain_agent.utils.store_detail")
#     @patch("langchain_agent.utils.User")
#     def test_run_llm_pipeline_store_node(
#         self, mock_user_model, mock_store_detail, mock_log_point
#     ):
#         chat_id = 1
#         message_id = 1
#         user_message_type = "text"

#         # Mock latest user message
#         mock_user_message_obj = MagicMock()
#         mock_user_message_obj.message_text = (
#             "Give my horoscope male bangalore 11 am 25-09-2001"
#         )
#         mock_user_query = MagicMock()
#         mock_user_query.latest.return_value = mock_user_message_obj

#         # ----- Mock latest bot message -----
#         mock_bot_message_obj = MagicMock()
#         mock_bot_message_obj.message_text = "This is the latest bot message"
#         mock_bot_query = MagicMock()
#         mock_bot_query.order_by.return_value.first.return_value = mock_bot_message_obj

#         # ----- Patch store_detail.objects.filter to return the right mock -----
#         def filter_side_effect(*args, **kwargs):

#             if kwargs.get("metric") == "user_message":
#                 return mock_user_query
#             elif kwargs.get("metric") == "bot_message":
#                 return mock_bot_query
#             return MagicMock()

#         mock_store_detail.objects.filter.side_effect = filter_side_effect

#         #     mock_call_litellm.return_value = (
#         #     "LLM generated response content",  # content
#         #     "gpt-4",                          # model_name
#         #     "v1",                             # model_version
#         #     100,                              # tokens
#         #     0.02                              # cost
#         # )
#         mock_user_instance = MagicMock()
#         mock_user_instance.user_profile = {}

#         mock_user_model.objects.get_or_create.return_value = (mock_user_instance, True)

#         # ----- Also mock setattr and save if needed -----
#         mock_user_instance.save = MagicMock()

#         # Act
#         result = store_in_db_node(
#             chat_id, "daily horoscope", message_id, user_message_type
#         )
#         self.assertEqual(result, "daily horoscope")
#         mock_log_point.assert_called()

#     # # @patch("langchain_agent.utils.log_point_to_db")
#     # # @patch("langchain_agent.utils.store_in_db_node")
#     # # @patch("langchain_agent.utils.call_litellm")
#     # # @patch("langchain_agent.utils.store_detail")
#     # # @patch("langchain_agent.utils.User")
#     # # def test_run_llm_pipeline_q_and_a_kundli(
#     # #     self,
#     # #     mock_user_model,
#     # #     mock_store_detail,
#     # #     mock_call_litellm,
#     # #     mock_store_in_db,
#     # #  mock_log_point,

#     # # ):
#     # #     chat_id = 1
#     # #     message_id = 1
#     # #     user_message_type = "text"

#     # #     # Mock latest user message
#     # #     mock_user_message_obj = MagicMock()
#     # #     mock_user_message_obj.message_text = "Give my horoscope male bangalore 11 am 25-09-2001"
#     # #     mock_user_query = MagicMock()
#     # #     mock_user_query.latest.return_value = mock_user_message_obj

#     # #     # ----- Mock latest bot message -----
#     # #     mock_bot_message_obj = MagicMock()
#     # #     mock_bot_message_obj.message_text = "This is the latest bot message"
#     # #     mock_bot_query = MagicMock()
#     # #     mock_bot_query.order_by.return_value.first.return_value = mock_bot_message_obj

#     # #     # ----- Patch store_detail.objects.filter to return the right mock -----
#     # #     def filter_side_effect(*args, **kwargs):

#     # #         if kwargs.get("metric") == "user_message":
#     # #             return mock_user_query
#     # #         elif kwargs.get("metric") == "bot_message":
#     # #             return mock_bot_query
#     # #         return MagicMock()

#     # #     mock_store_detail.objects.filter.side_effect = filter_side_effect

#     # #     mock_call_litellm.return_value = (
#     # #     "LLM generated response content",  # content
#     # #     "gpt-4",                          # model_name
#     # #     "v1",                             # model_version
#     # #     100,                              # tokens
#     # #     0.02                              # cost
#     # # )
#     # #     # mock_user_instance = MagicMock()
#     # #     # mock_user_instance.user_profile = {}

#     # #     # mock_user_model.objects.get_or_create.return_value = (mock_user_instance, True)

#     # #     # # ----- Also mock setattr and save if needed -----
#     # #     # mock_user_instance.save = MagicMock()

#     # #         # Act
#     # #     result = q_and_a_kundli_node(chat_id, message_id, user_message_type)

#     # #     mock_store_in_db.assert_called_once_with(chat_id,'LLM generated response content',message_id,user_message_type)

#     # @patch("langchain_agent.pdf_utils.generate_pdf.s3.upload_file")   
#     # @patch(
#     #     "langchain_agent.pdf_utils.generate_pdf.store_kundli_in_db",
#     #     new_callable=AsyncMock,
#     # )
#     # @patch(
#     #     "langchain_agent.pdf_utils.generate_pdf.store_key_value_pair_kundli_in_db",
#     #     new_callable=AsyncMock,
#     # )
#     # @patch("langchain_agent.pdf_utils.generate_pdf.main", new_callable=AsyncMock)
#     # @patch(
#     #     "langchain_agent.pdf_utils.generate_pdf.generate_mobile_friendly_kundli",
#     #     new_callable=AsyncMock,
#     # )
#     # @patch("langchain_agent.pdf_utils.generate_pdf.log_point_to_db")
#     # def test_run_llm_pipeline_call_kundli(
#     #     self,
#     #     mock_log,
#     #     mock_generate,
#     #     mock_main,
#     #     mock_store_key_value,
#     #     mock_store_kundli,
#     #     mock_upload_file
#     # ):
#     #     chat_id = 1
#     #     message_id = 1
#     #     user_message_type = "text"
#     #     mock_main.return_value = "data"
#     #     output_path = "1_kundli.pdf"

#     #     # Mock latest user message

#     #     result = call_divine(
#     #         {
#     #             "full_name": "Raghu",
#     #             "gender": "male",
#     #             "lat": "12.962940849999999",
#     #             "lon": "77.57575988493524",
#     #             "tzone": "5.5",
#     #             "day": "25",
#     #             "month": "9",
#     #             "year": "2001",
#     #             "hour": "11",
#     #             "min": "00",
#     #             "sec": "00",
#     #             "place": "Bangalore",
#     #         },
#     #         chat_id,
#     #         message_id,
#     #         user_message_type,
#     #     )

#     #     # mock_store_in_db.assert_called_once_with(chat_id,'LLM generated response content',message_id,user_message_type)

#     #     mock_store_kundli.assert_awaited_once_with("data", chat_id)
#     #     mock_store_key_value.assert_awaited_once_with("data", chat_id)
#     #     mock_generate.assert_awaited_once_with("data", chat_id, output_path=output_path)
#     #     mock_upload_file.assert_called_once_with(
#     #     "1_kundli.pdf",
#     #     "astro-ai",
#     #     "1_kundli.pdf",
#     #     ExtraArgs={"ACL": "public-read", "ContentType": "application/pdf"},
#     # )

#     #     mock_log.assert_called()

#     @patch("langchain_agent.pdf_utils.generate_pdf.s3.upload_file")   
#     @patch("langchain_agent.pdf_utils.generate_pdf.store_kundli_in_db", new_callable=AsyncMock)
#     @patch("langchain_agent.pdf_utils.generate_pdf.store_key_value_pair_kundli_in_db", new_callable=AsyncMock)
#     @patch("langchain_agent.pdf_utils.generate_pdf.main", new_callable=AsyncMock)
#     @patch("langchain_agent.pdf_utils.generate_pdf.generate_mobile_friendly_kundli", new_callable=AsyncMock)
#     @patch("langchain_agent.pdf_utils.generate_pdf.log_point_to_db")
#     @patch("langchain_agent.pdf_utils.generate_pdf.requests.post")
#     @patch("langchain_agent.utils.after_kundli_node")   # PATCH requests where it's imported
#     def test_run_llm_pipeline_call_kundli(
#         self,
#         mock_after_kundli_node,
#         mock_requests_post,
#         mock_log_point,
#         mock_generate_mobile,
#         mock_main,
#         mock_store_key_value,
#         mock_store_kundli,
#         mock_upload_file
#     ):
#         # Setup test input
#         chat_id = 1
#         message_id = 1
#         user_message_type = "text"
#         output_path = f"{chat_id}_kundli.pdf"

#         # Mock main() output since you're calling asyncio.run(main())
#         mock_main.return_value = "data"

#         # Mock DivineAPI requests.post() to prevent real HTTP call
#         mock_response = MagicMock()
#         mock_response.status_code = 200
#         mock_response.json.return_value = {"dummy": "divine response"}
#         mock_requests_post.return_value = mock_response

#         # Prepare payload for call_divine
#         payload = {
#             "full_name": "Raghu",
#             "gender": "male",
#             "lat": "12.962940849999999",
#             "lon": "77.57575988493524",
#             "tzone": "5.5",
#             "day": "25",
#             "month": "9",
#             "year": "2001",
#             "hour": "11",
#             "min": "00",
#             "sec": "00",
#             "place": "Bangalore",
#         }

#         # Act: Run the actual function
#         result = call_divine(payload, chat_id, message_id, user_message_type)

#         # Assert: Verify all expected mocks were called
#         mock_main.assert_called_once()

#         mock_store_kundli.assert_awaited_once_with("data", chat_id)
#         mock_store_key_value.assert_awaited_once_with("data", chat_id)
#         mock_generate_mobile.assert_awaited_once_with("data", chat_id, output_path=output_path)
#         mock_upload_file.assert_called_once_with(
#             f"{chat_id}_kundli.pdf",
#             "astro-ai",
#             f"{chat_id}_kundli.pdf",
#             ExtraArgs={"ACL": "public-read", "ContentType": "application/pdf"},
#         )
#         # mock_log_point.assert_called_with(
# #     health_metric="kundli_tool_node",
# #     phase="divine_api_time",
# #     latency=unittest.mock.ANY,  # Because latency is dynamic, we allow any value
# #     success=True
# # )
# #         mock_log_point.assert_any_call(
# #         health_metric="kundli_tool_node",
# #         phase="html_to_pdf_time",
# #         latency=unittest.mock.ANY,
# #         success=True
# #     )
# #         mock_log_point.assert_any_call(
# #     health_metric="kundli_tool_node",
# #     phase="store_in_db_time",
# #     latency=unittest.mock.ANY,
# #     success=True
# # )
# #         mock_log_point.assert_any_call(
# #     health_metric="kundli_tool_node",
# #     phase="s3_upload_time",
# #     latency=unittest.mock.ANY,
# #     success=True
# # )

#         mock_log_point.assert_any_call(
#     health_metric="kundli_tool_node",
#     phase="total_time",
#     latency=unittest.mock.ANY,
#     success=True
# )
#         mock_after_kundli_node.assert_called_once_with(chat_id, message_id, user_message_type)
        
# #         mock_log_point.assert_called()
#     @patch("langchain_agent.pdf_utils.generate_pdf.log_point_to_db")
#     @patch("langchain_agent.pdf_utils.generate_pdf.requests.post")
#     @patch('langchain_agent.utils.after_horoscope_node')
#     def test_run_llm_pipeline_call_horosocpe(
#         self,
#         mock_after_horoscope,
#         mock_post,
#         mock_log,
#     ):
#         chat_id = 1
#         message_id = 1
#         user_message_type = "text"
#         output_path = "1_kundli.pdf"

#         mock_response_roxy = MagicMock()
#         mock_response_roxy.status_code = 200
#         mock_response_roxy.json.return_value = {
#             "name": "Raghu",
#             "zodiac_sign": "Libra",
#             "personality": "Diplomatic, charming, and harmonious...",
#             "symbol": "♎",
#             "element": "Air",
#             "modality": "Cardinal",
#             "image": "https://cdn.roxyapi.com/img/astrology/libra.png",
#         }

#         mock_response_divine = MagicMock()
#         mock_response_divine.status_code = 200
#         mock_response_divine.json.return_value = {
#             "success": 1,
#             "data": {
#                 "sign": "Libra",
#                 "prediction": {
#                     "personal": "Relationships blossom today...",
#                     "health": "Focus on maintaining balance...",
#                     "profession": "Today, you might find yourself...",
#                     "emotions": "Emotional balance is key today...",
#                     "travel": "Today is favorable for short trips...",
#                     "luck": [
#                         "Colors of the day : Blue, Green",
#                         "Lucky Numbers of the day : 7, 14, 21",
#                         "Lucky Alphabets you will be in sync with : L, R",
#                         "Cosmic Tip : Stay open-minded today...",
#                         "Tips for Singles : Embrace new experiences...",
#                         "Tips for Couples : Communication is vital...",
#                     ],
#                 },
#                 "special": {"lucky_color_codes": ["#0000FF", "#008000"]},
#             },
#         }

#         def post_side_effect(url, *args, **kwargs):

#             if "roxyapi.com" in url:
#                 return mock_response_roxy
#             elif "astroapi-5.divineapi.com" in url:
#                 return mock_response_divine
#             else:
#                 raise ValueError("Unexpected URL in test")

#         mock_post.side_effect = post_side_effect

#         # Act
#         result = call_horoscope(
#             {"name": "Raghu", "dob": "2001-09-25", "time": "11:00:00"},
#             chat_id,
#             "daily horoscope",
#             message_id,
#             user_message_type,
#         )

#         # Assert that logging occurred
#         mock_log.assert_called()
#         mock_after_horoscope.assert_called_once_with(chat_id, message_id, user_message_type,'daily horoscope',{'data': {'name': 'Raghu', 'zodiac_sign': 'Libra', 'predictions': {'personal': 'Relationships blossom today...', 'health': 'Focus on maintaining balance...', 'profession': 'Today, you might find yourself...', 'emotions': 'Emotional balance is key today...', 'travel': 'Today is favorable for short trips...', 'luck': ['Colors of the day : Blue, Green', 'Lucky Numbers of the day : 7, 14, 21', 'Lucky Alphabets you will be in sync with : L, R', 'Cosmic Tip : Stay open-minded today...', 'Tips for Singles : Embrace new experiences...', 'Tips for Couples : Communication is vital...']}}})


# # # #         # Assert


# # # #         # Assert


# # # # #         # Assert
