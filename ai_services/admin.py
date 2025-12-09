from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import AIServiceConfig

class AIServiceConfigAdminForm(forms.ModelForm):
    """
    Custom form for AIServiceConfig that dynamically updates model version options
    and voice options based on the selected providers.
    """
    # Hidden fields to store initial values
    initial_stt_model_version = forms.CharField(widget=forms.HiddenInput(), required=False)
    initial_translation_model_version = forms.CharField(widget=forms.HiddenInput(), required=False)
    initial_tts_model_version = forms.CharField(widget=forms.HiddenInput(), required=False)
    initial_tts_voice = forms.CharField(widget=forms.HiddenInput(), required=False)
    initial_llm_model_version = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = AIServiceConfig
        fields = '__all__'
        widgets = {
            # STT widgets
            'stt_provider': forms.Select(attrs={'id': 'stt_provider_select'}),
            'stt_model_version': forms.Select(attrs={'id': 'stt_model_version_select'}),
            
            # Translation widgets
            'translation_provider': forms.Select(attrs={'id': 'translation_provider_select'}),
            'translation_model_version': forms.Select(attrs={'id': 'translation_model_version_select'}),
            
            # TTS widgets
            'tts_provider': forms.Select(attrs={'id': 'tts_provider_select'}),
            'tts_model_version': forms.Select(attrs={'id': 'tts_model_version_select'}),
            'tts_voice': forms.Select(attrs={'id': 'tts_voice_select'}),
            
            # LLM widgets
            'llm_provider': forms.Select(attrs={'id': 'llm_provider_select'}),
            'llm_model_version': forms.Select(attrs={'id': 'llm_model_version_select'}),
            
            # Common settings
            'temperature': forms.NumberInput(attrs={
                'id': 'temperature_input',
                'step': '0.1',
                'min': '0.0',
                'max': '1.0'
            }),
        }
        help_texts = {
            'temperature': 'Choose a temperature value between 0.0 and 1.0'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get instance if it exists
        instance = kwargs.get('instance')
        
        # Default empty choices for all select fields
        empty_choice = [('', '--------')]
        
        # Set initial choices for all model versions and voice selects
        self.fields['stt_model_version'].choices = empty_choice
        self.fields['translation_model_version'].choices = empty_choice
        self.fields['tts_model_version'].choices = empty_choice
        self.fields['tts_voice'].choices = empty_choice
        self.fields['llm_model_version'].choices = empty_choice
        
        # Set choices and store initial values if instance exists
        if instance:  # Check if editing an existing instance
            # STT
            if instance.stt_provider:
                self.fields['stt_model_version'].choices = (
                    empty_choice + AIServiceConfig.MODEL_VERSIONS.get(instance.stt_provider, [])
                )
                self.initial['initial_stt_model_version'] = instance.stt_model_version
                
                # Add data attribute to help JavaScript
                self.fields['stt_model_version'].widget.attrs['data-initial-value'] = instance.stt_model_version

            # Translation
            if instance.translation_provider:
                self.fields['translation_model_version'].choices = (
                    empty_choice + AIServiceConfig.TRANSLATION_MODEL_VERSIONS.get(instance.translation_provider, [])
                )
                self.initial['initial_translation_model_version'] = instance.translation_model_version
                self.fields['translation_model_version'].widget.attrs['data-initial-value'] = instance.translation_model_version

            # TTS
            if instance.tts_provider:
                self.fields['tts_model_version'].choices = (
                    empty_choice + AIServiceConfig.TTS_MODEL_VERSIONS.get(instance.tts_provider, [])
                )
                self.initial['initial_tts_model_version'] = instance.tts_model_version
                self.fields['tts_model_version'].widget.attrs['data-initial-value'] = instance.tts_model_version

                self.fields['tts_voice'].choices = (
                    empty_choice + AIServiceConfig.VOICES.get(instance.tts_provider, [])
                )
                self.initial['initial_tts_voice'] = instance.tts_voice
                self.fields['tts_voice'].widget.attrs['data-initial-value'] = instance.tts_voice

            # LLM
            if instance.llm_provider:
                self.fields['llm_model_version'].choices = (
                    empty_choice + AIServiceConfig.LLM_MODEL_VERSIONS.get(instance.llm_provider, [])
                )
                self.initial['initial_llm_model_version'] = instance.llm_model_version
                self.fields['llm_model_version'].widget.attrs['data-initial-value'] = instance.llm_model_version

    def clean(self):
        cleaned_data = super().clean()
        
        # If initial values were provided but the form didn't update them,
        # use the initial values
        if not cleaned_data.get('stt_model_version') and cleaned_data.get('initial_stt_model_version'):
            cleaned_data['stt_model_version'] = cleaned_data['initial_stt_model_version']
            
        if not cleaned_data.get('translation_model_version') and cleaned_data.get('initial_translation_model_version'):
            cleaned_data['translation_model_version'] = cleaned_data['initial_translation_model_version']
            
        if not cleaned_data.get('tts_model_version') and cleaned_data.get('initial_tts_model_version'):
            cleaned_data['tts_model_version'] = cleaned_data['initial_tts_model_version']
            
        if not cleaned_data.get('tts_voice') and cleaned_data.get('initial_tts_voice'):
            cleaned_data['tts_voice'] = cleaned_data['initial_tts_voice']
            
        if not cleaned_data.get('llm_model_version') and cleaned_data.get('initial_llm_model_version'):
            cleaned_data['llm_model_version'] = cleaned_data['initial_llm_model_version']
            
        return cleaned_data
                # self.fields['llm_model_version'].initial = self.instance.llm_model_version  # Set initial value
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    #     empty_choice = [('', '--------')]
    #     instance = kwargs.get('instance')

    #     # STT
    #     stt_choices = AIServiceConfig.MODEL_VERSIONS.get(instance.stt_provider, []) if instance and instance.stt_provider else []
    #     if instance and instance.stt_model_version and (instance.stt_model_version, instance.stt_model_version) not in stt_choices:
    #         stt_choices.append((instance.stt_model_version, instance.stt_model_version))
    #     self.fields['stt_model_version'].choices = empty_choice + stt_choices

    #     # Translation
    #     trans_choices = AIServiceConfig.TRANSLATION_MODEL_VERSIONS.get(instance.translation_provider, []) if instance and instance.translation_provider else []
    #     if instance and instance.translation_model_version and (instance.translation_model_version, instance.translation_model_version) not in trans_choices:
    #         trans_choices.append((instance.translation_model_version, instance.translation_model_version))
    #     self.fields['translation_model_version'].choices = empty_choice + trans_choices

    #     # TTS Model Version
    #     tts_model_choices = AIServiceConfig.TTS_MODEL_VERSIONS.get(instance.tts_provider, []) if instance and instance.tts_provider else []
    #     if instance and instance.tts_model_version and (instance.tts_model_version, instance.tts_model_version) not in tts_model_choices:
    #         tts_model_choices.append((instance.tts_model_version, instance.tts_model_version))
    #     self.fields['tts_model_version'].choices = empty_choice + tts_model_choices

    #     # TTS Voice
    #     voice_choices = AIServiceConfig.VOICES.get(instance.tts_provider, []) if instance and instance.tts_provider else []
    #     if instance and instance.tts_voice and (instance.tts_voice, instance.tts_voice) not in voice_choices:
    #         voice_choices.append((instance.tts_voice, instance.tts_voice))
    #     self.fields['tts_voice'].choices = empty_choice + voice_choices

    #     # LLM
    #     llm_choices = AIServiceConfig.LLM_MODEL_VERSIONS.get(instance.llm_provider, []) if instance and instance.llm_provider else []
    #     if instance and instance.llm_model_version and (instance.llm_model_version, instance.llm_model_version) not in llm_choices:
    #         llm_choices.append((instance.llm_model_version, instance.llm_model_version))
    #     self.fields['llm_model_version'].choices = empty_choice + llm_choices




class AIServiceConfigAdmin(admin.ModelAdmin):
    form = AIServiceConfigAdminForm
    
    fieldsets = (
        ('Speech-to-Text Configuration', {
            'fields': ('stt_provider', 'stt_model_version'),
            'classes': ('wide',),
        }),
        ('Translation Configuration', {
            'fields': ('translation_provider', 'translation_model_version'),
            'classes': ('wide',),
        }),
        ('Text-to-Speech Configuration', {
            'fields': ('tts_provider', 'tts_model_version', 'tts_voice'),
            'classes': ('wide',),
        }),
        ('Large Language Model Configuration', {
            'fields': ('llm_provider', 'llm_model_version', 'temperature'),
            'classes': ('wide',),
        }),
        ('Status', {
            'fields': ('is_active',),
            'classes': ('wide',),
        }),
    )
    
    list_display = (
        'id', 
        'created_at', 
        'stt_provider',
        'get_stt_model_version_label',
        'translation_provider',
        'get_translation_model_version_label', 
        'tts_provider',
        'get_tts_model_version_label',
        'get_tts_voice_label',
        'llm_provider',
        'get_llm_model_version_label',
        'temperature',
        'is_active'
    )

    list_filter = ('is_active', 'stt_provider', 'translation_provider', 'tts_provider', 'llm_provider')
    search_fields = ('stt_provider', 'translation_provider', 'tts_provider', 'llm_provider')
    readonly_fields = ('created_at', 'updated_at')

    def get_stt_model_version_label(self, obj):
        return dict(AIServiceConfig.MODEL_VERSIONS.get(obj.stt_provider, [])).get(obj.stt_model_version, obj.stt_model_version)
    get_stt_model_version_label.short_description = "STT Model Version"

    def get_translation_model_version_label(self, obj):
        return dict(AIServiceConfig.TRANSLATION_MODEL_VERSIONS.get(obj.translation_provider, [])).get(obj.translation_model_version, obj.translation_model_version)
    get_translation_model_version_label.short_description = "Translation Model Version"

    def get_tts_model_version_label(self, obj):
        return dict(AIServiceConfig.TTS_MODEL_VERSIONS.get(obj.tts_provider, [])).get(obj.tts_model_version, obj.tts_model_version)
    get_tts_model_version_label.short_description = "TTS Model Version"

    def get_tts_voice_label(self, obj):
        return dict(AIServiceConfig.VOICES.get(obj.tts_provider, [])).get(obj.tts_voice, obj.tts_voice)
    get_tts_voice_label.short_description = "TTS Voice"

    def get_llm_model_version_label(self, obj):
        return dict(AIServiceConfig.LLM_MODEL_VERSIONS.get(obj.llm_provider, [])).get(obj.llm_model_version, obj.llm_model_version)
    get_llm_model_version_label.short_description = "LLM Model Version"
        
    class Media:
        js = ('js/ai_service_config_admin.js',)
        
    def save_model(self, request, obj, form, change):
        """If setting this config as active, deactivate all others"""
        if obj.is_active:
            AIServiceConfig.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)


admin.site.register(AIServiceConfig, AIServiceConfigAdmin)