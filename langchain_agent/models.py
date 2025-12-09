from django.db import models

from django.utils.timezone import now
from enum import Enum
from enumfields import EnumField
from enum import Enum

# Create your models here.
class User(models.Model):
    user_profile = models.JSONField(
        verbose_name="User Profile",
        default=dict,
        blank=True,
        help_text="Stores user profile information as JSON data."
    )
    family_details=models.JSONField(
        verbose_name="Family detail",
        default=dict,
        blank=True,
        help_text="Stores family detailed information as JSON data."
    )
    health_details=models.JSONField(
        verbose_name="health detail",
        default=dict,
        blank=True,
        help_text="Stores health information as JSON data."
    )

    horoscope_details = models.JSONField(
        verbose_name="Horoscope Details",
        default=dict,
        blank=True,
        help_text="Stores user horoscope details as JSON data."
    )
    kundli_details = models.JSONField(
        verbose_name="Kundli Details",
        default=dict,
        blank=True,
        help_text="Stores user kundli details as JSON data."
    )
    financial_details=models.JSONField( verbose_name="Financial Details",
        default=dict,
        blank=True,
        help_text="Stores user financial details as JSON data.")
    general_astrology_details=models.JSONField( verbose_name="General Astrology Details",
        default=dict,
        blank=True,
        help_text="Stores user general astrology details as JSON data.")
    basic_astro_details = models.JSONField(default=dict, blank=True)
    planetary_positions = models.JSONField(default=dict, blank=True)
    sub_planet_positions = models.JSONField(default=dict, blank=True)
    sadhe_sati = models.JSONField(default=dict, blank=True)
    kaal_sarpa_yoga = models.JSONField(default=dict, blank=True)
    manglik_dosha = models.JSONField(default=dict, blank=True)
    composite_friendship = models.JSONField(default=dict, blank=True)
    shadbala = models.JSONField(default=dict, blank=True)
    ascendant_report = models.JSONField(default=dict, blank=True)
    yogas = models.JSONField(default=dict, blank=True)
    kaal_chakra_dasha = models.JSONField(default=dict, blank=True)
    ghata_chakra = models.JSONField(default=dict, blank=True)
    yogini_dasha = models.JSONField(default=dict, blank=True)
    sub_planet_chart = models.JSONField(default=dict, blank=True)
    sudarshana_chakra = models.JSONField(default=dict, blank=True)
    horoscope_chart = models.JSONField(default=dict, blank=True)
    bhava_kundli = models.JSONField(default=dict, blank=True)
    vimshottari_dasha = models.JSONField(default=dict, blank=True, verbose_name="Vimshottari Dasha")
    mahadasha_analysis = models.JSONField(default=dict, blank=True, verbose_name="Maha Dasha Analysis")
    antardasha_analysis = models.JSONField(default=dict, blank=True, verbose_name="Antar Dasha Analysis")
    pratyantardasha_analysis = models.JSONField(default=dict, blank=True, verbose_name="Pratyantar Dasha Analysis")
    kundli_flow = models.BooleanField(default=False) 
    daily_horoscope_flow = models.BooleanField(default=False) 
    weekly_horoscope_flow = models.BooleanField(default=False)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Return the username if present in the JSON, otherwise a default string.
        return self.user_profile.get("username", "Unnamed User")
    

class LogType(Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"
    
class Logger(models.Model):
    

    id = models.AutoField(primary_key=True)
    user_id=models.TextField()
    message = models.TextField()
    log_type = EnumField(LogType, default=LogType.SYSTEM)
    message_id=models.TextField(null=True)
    callback_query_id=models.TextField(null=False,default='NULL')
    # log_type = models.CharField(
    #     max_length=10,
    #     choices=LogType.choices,
    #     default=LogType.SYSTEM,  # Default to system logs
    # )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# class pipeline_log(models.Model):
#     graph_compile_time=models.FloatField(null=True,default=0)
#     create_user_time=models.FloatField(null=True,default=0)
#     graph_intent_node_total_time=models.FloatField(null=True,default=0)
#     graph_intent_node_llm_time=models.FloatField(null=True,default=0)
#     graph_decision_node_total_time=models.FloatField(null=True,default=0)
#     graph_conversation_node_total_time=models.FloatField(null=True,default=0)
#     graph_conversation_node_llm_time=models.FloatField(null=True,default=0)
#     graph_kundli_node_llm1_time=models.FloatField(null=True,default=0)
#     graph_kundli_node_llm2_time=models.FloatField(null=True,default=0)
#     graph_kundli_node_total_time=models.FloatField(null=True,default=0)
#     graph_horoscope_node_total_time=models.FloatField(null=True,default=0)
#     graph_horoscope_node_llm1_time=models.FloatField(null=True,default=0)
#     graph_horoscope_node_llm2_time=models.FloatField(null=True,default=0)
#     graph_horoscope_tool_node_total_time=models.FloatField(null=True,default=0)
#     graph_horoscope_tool_node_divine_api_time=models.FloatField(null=True,default=0)
#     graph_kundli_tool_node_total_time=models.FloatField(null=True,default=0)
#     graph_kundli_tool_node_divine_api_time=models.FloatField(null=True,default=0) 
#     # graph_kundli_tool_node_jinja_render_time=models.FloatField(null=True,default=0)
#     graph_kundli_tool_node_html_to_pdf_time=models.FloatField(null=True,default=0)
#     graph_kundli_tool_node_s3_upload_time=models.FloatField(null=True,default=0)
#     graph_kundli_tool_node_s3_download_time=models.FloatField(null=True,default=0)
#     graph_kundli_tool_node_db_store_time=models.FloatField(null=True,default=0)
#     graph_after_kundli_node_total_time=models.FloatField(null=True,default=0)
#     graph_after_horoscope_node_total_time=models.FloatField(null=True,default=0)
#     graph_after_horoscope_node_llm_time=models.FloatField(null=True,default=0)
#     graph_store_in_db_node_total_time=models.FloatField(null=True,default=0)
#     graph_store_in_db_db_time=models.FloatField(null=True,default=0)
#     graph_store_in_db_node_llm_time=models.FloatField(null=True,default=0)


class store_detail(models.Model):
    id = models.AutoField(primary_key=True)
    message_text=models.TextField(null=False,default='NULL')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stored_details')
    metric=models.TextField(null=False,default='NULL')
    # message= models.ForeignKey(Logger, on_delete=models.CASCADE, related_name='store_details')
    message_id=models.TextField(null=False,default='NULL')
    message_type=models.TextField(null=False,default='NULL')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)









    







