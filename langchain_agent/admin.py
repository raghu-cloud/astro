from django.contrib import admin

# Register your models here.
from django.utils.safestring import mark_safe
from django.contrib.postgres.fields import JSONField
from django_json_widget.widgets import JSONEditorWidget as PrettyJSONWidget
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget},
    }
    
    list_display = ('display_user_profile', 'display_family_details', 'display_health_details', 'display_horoscope_details', 'display_kundli_details', 'display_financial_details', 'display_general_astrology_details')
    search_fields = ['user_profile__username']

    def format_json(self, json_data):
        """Helper function to format JSON as an HTML preformatted block."""
        return mark_safe(f'<pre>{json_data}</pre>') if json_data else "N/A"

    @admin.display(description="User Profile")
    def display_user_profile(self, obj):
        return self.format_json(obj.user_profile)

    @admin.display(description="Family Details")
    def display_family_details(self, obj):
        return self.format_json(obj.family_details)

    @admin.display(description="Health Details")
    def display_health_details(self, obj):
        return self.format_json(obj.health_details)

    @admin.display(description="Horoscope Details")
    def display_horoscope_details(self, obj):
        return self.format_json(obj.horoscope_details)

    @admin.display(description="Kundli Details")
    def display_kundli_details(self, obj):
        return self.format_json(obj.kundli_details)

    @admin.display(description="Financial Details")
    def display_financial_details(self, obj):
        return self.format_json(obj.financial_details)

    @admin.display(description="General Astrology Details")
    def display_general_astrology_details(self, obj):
        return self.format_json(obj.general_astrology_details)
