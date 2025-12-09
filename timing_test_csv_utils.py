import os
import csv
from datetime import datetime

CSV_LOG_PATH = os.path.join(os.path.dirname(__file__), 'timing_logs.csv')

def log_time_to_csv(chat_id, message_type, message_id, stage, duration):
    file_exists = os.path.isfile(CSV_LOG_PATH)
    with open(CSV_LOG_PATH, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['chat_id', 'message_type', 'message_id', 'stage', 'duration_sec', 'timestamp'])
        writer.writerow([chat_id, message_type, message_id, stage, round(duration, 3), datetime.now().isoformat()])


def calculate_average_initial_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'initial':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_processing_time_text(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'processing' and row['message_type'] == 'text':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    continue

    return round(total_time / count, 3) if count > 0 else 0

def calculate_average_processing_time_voice(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'processing' and row['message_type'] == 'voice':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    continue

    return round(total_time / count, 3) if count > 0 else 0

def average_download_voice(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'download_voice' and row['message_type'] == 'voice':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    continue

    return round(total_time / count, 3) if count > 0 else 0

def average_summarization_for_voice(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'summarization_for_voice' and row['message_type'] == 'voice':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    continue

    return round(total_time / count, 3) if count > 0 else 0

def average_STT(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'STT' and row['message_type'] == 'voice':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    continue

    return round(total_time / count, 3) if count > 0 else 0

def average_TTS(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'TTS' and row['message_type'] == 'voice':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    continue

    return round(total_time / count, 3) if count > 0 else 0


def calculate_average_language_translation(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'language_translation':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)


def calculate_average_langraph_pipeline_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'langraph_pipeline_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)


def calculate_average_core_langraph_pipeline_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'core_langraph_pipeline_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)


def calculate_average_langraph_compilation_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'langraph_compilation_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_user_db_get_create_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'user_db_get_create_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_langraph_execution_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'langraph_execution_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)


def calculate_average_langraph_execution_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'langraph_execution_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_kundli_pdf_send_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'kundli_pdf_send_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)


def calculate_average_llm_call_chatbot(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'llm_call_chatbot':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_chatbot_total_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'chatbot_total_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_pre_llm_template_call4(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'pre_llm_template_call4':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_llm_call_kundli_call4(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'llm_call_kundli_call4':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_llm_missing_kundli_details_call4(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'llm_missing_kundli_details_call4':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_kundli_total_time_call4_no_llm_invoke(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'kundli_total_time_call4_no_llm_invoke':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)


def calculate_average_kundli_total_time_call4(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'kundli_total_time_call4':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_llm_call_conversation(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'llm_call_conversation':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_conversation_total_time_call2(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'conversation_total_time_call2':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_llm_call_summary_call3(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'llm_call_summary_call3':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)


def calculate_average_llm_call_horoscope_details_call3(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'llm_call_horoscope_details_call3':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_llm_call_missing_details_call3(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'llm_call_missing_details_call3':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_horoscope_total_time_call3(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'horoscope_total_time_call3':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)



def calculate_average_llm_call_kundli_followup(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'llm_call_kundli_followup':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)


def calculate_average_kundli_followup_total_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'kundli_followup_total_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)


def calculate_average_llm_call_store_user_details_db(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'llm_call_store_user_details_db':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_store_user_details_db_total_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'store_user_details_db_total_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_kundli_api_requests_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'kundli_api_requests_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)


def calculate_average_kundli_jinja_render(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'kundli_jinja_render':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_kundli_pdf_generation(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'kundli_pdf_generation':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_kundli_data_db_store(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'kundli_data_db_store':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_kundli_pdf_s3_upload(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'kundli_pdf_s3_upload':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_kundli_tool_total_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'kundli_tool_total_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)

def calculate_average_horoscope_tool_total_time(csv_path):
    total_time = 0
    count = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['stage'] == 'horoscope_tool_total_time':
                try:
                    total_time += float(row['duration_sec'])
                    count += 1
                except ValueError:
                    pass  # skip rows with invalid number format

    if count == 0:
        return 0
    return round(total_time / count, 3)


# if __name__ == "__main__":
#     CSV_LOG_PATH = 'timing_logs_kundli.csv'
#     print("Initial time before message processing , fetching user message from telegram payload:", calculate_average_initial_time(CSV_LOG_PATH))
#     print("User message- text processing pipeline time", calculate_average_processing_time_text(CSV_LOG_PATH))
#     print("User message- voice processing pipeline time", calculate_average_processing_time_voice(CSV_LOG_PATH))
#     print("Langraph pipeline processing time- includes threading typing action", calculate_average_langraph_pipeline_time(CSV_LOG_PATH))
#     print("Total translation time of text into user language from english and vice versa:", calculate_average_language_translation(CSV_LOG_PATH))


#     print("Core Langraph pipeline processing time from (building graph to execution)", calculate_average_core_langraph_pipeline_time(CSV_LOG_PATH))
#     print("LangGraph compilation time", calculate_average_langraph_compilation_time(CSV_LOG_PATH))
#     print("User create or fetch from DB in langraph engine",calculate_average_user_db_get_create_time(CSV_LOG_PATH))
#     print("LangGraph pipeline execution time", calculate_average_langraph_execution_time(CSV_LOG_PATH))

#     print("User intent node - Total Time:",calculate_average_chatbot_total_time(CSV_LOG_PATH))
#     print("User intent node - LLM Time:",calculate_average_llm_call_chatbot(CSV_LOG_PATH))
#     print("Node processing- non LLM time:",calculate_average_chatbot_total_time(CSV_LOG_PATH) - calculate_average_llm_call_chatbot(CSV_LOG_PATH))

#     print("Normal conversation node - Total Time:", calculate_average_conversation_total_time_call2(CSV_LOG_PATH))
#     print("Normal conversation-LLM Time", calculate_average_llm_call_conversation(CSV_LOG_PATH))
#     print("Normal conversation processing - non LLM time:",calculate_average_conversation_total_time_call2(CSV_LOG_PATH) - calculate_average_llm_call_conversation(CSV_LOG_PATH))


#     print("Horoscope generation node - Total time:", calculate_average_horoscope_total_time_call3(CSV_LOG_PATH))
#     print("Horoscope generation -LLM Time:", (calculate_average_llm_call_summary_call3(CSV_LOG_PATH) + calculate_average_llm_call_horoscope_details_call3(CSV_LOG_PATH) + calculate_average_llm_call_missing_details_call3(CSV_LOG_PATH))/3)
#     print("Horoscope generation processing - non LLM time:", calculate_average_horoscope_total_time_call3(CSV_LOG_PATH)-((calculate_average_llm_call_summary_call3(CSV_LOG_PATH) + calculate_average_llm_call_horoscope_details_call3(CSV_LOG_PATH) + calculate_average_llm_call_missing_details_call3(CSV_LOG_PATH))/3))

#     print("Horoscope tool call - Total time:", calculate_average_horoscope_tool_total_time(CSV_LOG_PATH) )


#     print("Kundli Generation node - Total time:", calculate_average_kundli_total_time_call4(CSV_LOG_PATH))
#     print("Kundli Generation - LLM time:", (calculate_average_llm_call_kundli_call4(CSV_LOG_PATH)+calculate_average_llm_missing_kundli_details_call4(CSV_LOG_PATH))/2)
#     print("Kundli Generation processing - non LLM time:", calculate_average_kundli_total_time_call4(CSV_LOG_PATH) - ((calculate_average_llm_call_kundli_call4(CSV_LOG_PATH)+calculate_average_llm_missing_kundli_details_call4(CSV_LOG_PATH))/2))

#     print("Kundli tool call - total time:", calculate_average_kundli_tool_total_time(CSV_LOG_PATH))
#     print("Kundli API requests time:", calculate_average_kundli_api_requests_time(CSV_LOG_PATH))
#     print("Kundli jinja render time:", calculate_average_kundli_jinja_render(CSV_LOG_PATH))
#     print("Kundli pdf generation from html template time:", calculate_average_kundli_pdf_generation(CSV_LOG_PATH))
#     print("Kundli data in DB Storage time:", calculate_average_kundli_data_db_store(CSV_LOG_PATH))
#     print("Kundli pdf s3 upload time:", calculate_average_kundli_pdf_s3_upload(CSV_LOG_PATH))

#     print("Kundli Follow up node - Total time:", calculate_average_kundli_followup_total_time(CSV_LOG_PATH))
#     print("Kundli followup- LLM time:", calculate_average_llm_call_kundli_followup(CSV_LOG_PATH))
#     print("Kundli followup processing- non LLM time:",  calculate_average_kundli_followup_total_time(CSV_LOG_PATH)- calculate_average_llm_call_kundli_followup(CSV_LOG_PATH))

if __name__ == "__main__":
    print("Initial time before message processing , fetching user message from telegram payload:", calculate_average_initial_time(CSV_LOG_PATH))
    print("User message- text processing pipeline time", calculate_average_processing_time_text(CSV_LOG_PATH))
    print("User message- voice processing pipeline time", calculate_average_processing_time_voice(CSV_LOG_PATH))
    print("Langraph pipeline processing time- includes threading typing action", calculate_average_langraph_pipeline_time(CSV_LOG_PATH))
    print("Total translation time of text into user language from english and vice versa:", calculate_average_language_translation(CSV_LOG_PATH))

    print("Core Langraph pipeline processing time from (building graph to execution)", calculate_average_core_langraph_pipeline_time(CSV_LOG_PATH))
    print("LangGraph compilation time", calculate_average_langraph_compilation_time(CSV_LOG_PATH))
    print("User create or fetch from DB in langraph engine", calculate_average_user_db_get_create_time(CSV_LOG_PATH))
    print("LangGraph pipeline execution time", calculate_average_langraph_execution_time(CSV_LOG_PATH))

    # Chatbot node
    total_chatbot = calculate_average_chatbot_total_time(CSV_LOG_PATH)
    llm_chatbot = calculate_average_llm_call_chatbot(CSV_LOG_PATH)
    non_llm_chatbot = total_chatbot - llm_chatbot
    print("User intent node - Total Time:", total_chatbot)
    print("User intent node - LLM Time:", llm_chatbot)
    print("Node processing- non LLM time:", non_llm_chatbot)

    # Conversation node
    total_conv = calculate_average_conversation_total_time_call2(CSV_LOG_PATH)
    llm_conv = calculate_average_llm_call_conversation(CSV_LOG_PATH)
    non_llm_conv = total_conv - llm_conv
    print("Normal conversation node - Total Time:", total_conv)
    print("Normal conversation-LLM Time", llm_conv)
    print("Normal conversation processing - non LLM time:", non_llm_conv)

    # Horoscope node
    total_horo = calculate_average_horoscope_total_time_call3(CSV_LOG_PATH)
    llm_horo = (
        calculate_average_llm_call_summary_call3(CSV_LOG_PATH)
        + calculate_average_llm_call_horoscope_details_call3(CSV_LOG_PATH)
        + calculate_average_llm_call_missing_details_call3(CSV_LOG_PATH)
    ) / 3
    non_llm_horo = total_horo - llm_horo
    print("Horoscope generation node - Total time:", total_horo)
    print("Horoscope generation -LLM Time:", llm_horo)
    print("Horoscope generation processing - non LLM time:", non_llm_horo)

    # Horoscope tool
    print("Horoscope tool call - Total time:", calculate_average_horoscope_tool_total_time(CSV_LOG_PATH))

    # Kundli generation node
    total_kundli = calculate_average_kundli_total_time_call4(CSV_LOG_PATH)
    llm_kundli = (
        calculate_average_llm_call_kundli_call4(CSV_LOG_PATH)
        + calculate_average_llm_missing_kundli_details_call4(CSV_LOG_PATH)
    ) / 2
    non_llm_kundli = total_kundli - llm_kundli
    print("Kundli Generation node - Total time:", total_kundli)
    print("Kundli Generation - LLM time:", llm_kundli)
    print("Kundli Generation processing - non LLM time:", non_llm_kundli)

    # Kundli tool and steps
    print("Kundli tool call - total time:", calculate_average_kundli_tool_total_time(CSV_LOG_PATH))
    print("Kundli API requests time:", calculate_average_kundli_api_requests_time(CSV_LOG_PATH))
    print("Kundli jinja render time:", calculate_average_kundli_jinja_render(CSV_LOG_PATH))
    print("Kundli pdf generation from html template time:", calculate_average_kundli_pdf_generation(CSV_LOG_PATH))
    print("Kundli data in DB Storage time:", calculate_average_kundli_data_db_store(CSV_LOG_PATH))
    print("Kundli pdf s3 upload time:", calculate_average_kundli_pdf_s3_upload(CSV_LOG_PATH))

    # Kundli follow-up node
    total_followup = calculate_average_kundli_followup_total_time(CSV_LOG_PATH)
    llm_followup = calculate_average_llm_call_kundli_followup(CSV_LOG_PATH)
    non_llm_followup = total_followup - llm_followup
    print("Kundli Follow up node - Total time:", total_followup)
    print("Kundli followup- LLM time:", llm_followup)
    print("Kundli followup processing- non LLM time:", non_llm_followup)

    # Sum up all non-LLM times
    total_non_llm_time = (
        non_llm_chatbot
        + non_llm_conv
        + non_llm_horo
        + non_llm_kundli
        + non_llm_followup
        # You can also include other non-LLM steps if needed, e.g.
        # + calculate_average_processing_time_text(CSV_LOG_PATH)
        # + calculate_average_processing_time_voice(CSV_LOG_PATH)
        # etc.
    )
    print("Total non-LLM processing time across all nodes:", total_non_llm_time)

def average_api_time():
    total_time = (
        average_download_voice(CSV_LOG_PATH)
        + average_summarization_for_voice(CSV_LOG_PATH)
        + average_STT(CSV_LOG_PATH)
        + average_TTS(CSV_LOG_PATH)
        + calculate_average_language_translation(CSV_LOG_PATH)
        + calculate_average_kundli_pdf_send_time(CSV_LOG_PATH)
        + calculate_average_llm_call_chatbot(CSV_LOG_PATH)
        + calculate_average_llm_call_conversation(CSV_LOG_PATH)
        + calculate_average_llm_call_horoscope_details_call3(CSV_LOG_PATH)
        + calculate_average_kundli_api_requests_time(CSV_LOG_PATH)
        + calculate_average_pre_llm_template_call4(CSV_LOG_PATH)
        + calculate_average_llm_call_kundli_call4(CSV_LOG_PATH)
        + calculate_average_llm_call_kundli_followup(CSV_LOG_PATH)
        + calculate_average_llm_call_missing_details_call3(CSV_LOG_PATH)
        + calculate_average_llm_call_summary_call3(CSV_LOG_PATH)
        + calculate_average_kundli_pdf_s3_upload(CSV_LOG_PATH)
        + calculate_average_horoscope_tool_total_time(CSV_LOG_PATH)
        )
    print(total_time)

    return total_time

# def average_non_api_time():
#     # Sum up all non-LLM times
#     total_non_llm_time = (
#         non_llm_chatbot
#         + non_llm_conv
#         + non_llm_horo
#         + non_llm_kundli
#         + non_llm_followup
#         + calculate_average_kundli_pdf_generation(CSV_LOG_PATH)
#     )

#     return total_non_llm_time

def average_non_api_time():
    total_non_llm_time = (
        (calculate_average_chatbot_total_time(CSV_LOG_PATH) - calculate_average_llm_call_chatbot(CSV_LOG_PATH))
        + (calculate_average_conversation_total_time_call2(CSV_LOG_PATH) - calculate_average_llm_call_conversation(CSV_LOG_PATH))
        + (calculate_average_horoscope_total_time_call3(CSV_LOG_PATH)
           - (
               (calculate_average_llm_call_summary_call3(CSV_LOG_PATH)
                + calculate_average_llm_call_horoscope_details_call3(CSV_LOG_PATH)
                + calculate_average_llm_call_missing_details_call3(CSV_LOG_PATH)
               ) / 3
             ))
        + (calculate_average_kundli_total_time_call4(CSV_LOG_PATH)
           - (
               (calculate_average_llm_call_kundli_call4(CSV_LOG_PATH)
                + calculate_average_llm_missing_kundli_details_call4(CSV_LOG_PATH)
               ) / 2
             ))
        + (calculate_average_kundli_followup_total_time(CSV_LOG_PATH) - calculate_average_llm_call_kundli_followup(CSV_LOG_PATH))
        + calculate_average_kundli_pdf_generation(CSV_LOG_PATH)
    )
    return total_non_llm_time

