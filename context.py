import contextvars

msg_id_var = contextvars.ContextVar("request_id")
chat_id_var = contextvars.ContextVar("chat_id")
channel_var = contextvars.ContextVar("channel")
request_type_var = contextvars.ContextVar("message_type")

def set_request_context(msg_id, chat_id, channel, request_type):
    msg_id_var.set(msg_id)
    chat_id_var.set(chat_id)
    channel_var.set(channel)
    request_type_var.set(request_type)

def get_request_id():
    return msg_id_var.get(None)

def get_user_id():
    return chat_id_var.get(None)

def get_channel():
    return channel_var.get(None)

def get_request_type():
    return request_type_var.get(None)