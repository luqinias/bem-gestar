"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone

from .models import User, PatientProfile, DoctorProfile


class PatientProfileInline(admin.StackedInline):
    model = PatientProfile
    can_delete = False
    extra = 0


class DoctorProfileInline(admin.StackedInline):
    model = DoctorProfile
    can_delete = False
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'name', 'user_type', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_active', 'is_staff']
    search_fields = ['email', 'name']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações pessoais', {'fields': ('name', 'phone', 'date_of_birth', 'avatar')}),
        ('Tipo de usuário', {'fields': ('user_type',)}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'user_type', 'password1', 'password2'),
        }),
    )

    def get_inlines(self, request, obj=None):
        if obj:
            if obj.user_type == User.UserType.PATIENT:
                return [PatientProfileInline]
            elif obj.user_type == User.UserType.DOCTOR:
                return [DoctorProfileInline]
        return []


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'crm', 'crm_state', 'specialty', 'is_crm_validated', 'validation_date']
    list_filter = ['is_crm_validated', 'specialty', 'crm_state']
    search_fields = ['user__name', 'user__email', 'crm']
    actions = ['validate_crm', 'invalidate_crm']

    @admin.action(description='Validar CRM selecionados')
    def validate_crm(self, request, queryset):
        updated = queryset.update(is_crm_validated=True, validation_date=timezone.now())
        # Also activate the user account
        for profile in queryset:
            profile.user.is_active = True
            profile.user.save()
        self.message_user(request, f'{updated} CRM(s) validado(s) com sucesso.')

    @admin.action(description='Invalidar CRM selecionados')
    def invalidate_crm(self, request, queryset):
        updated = queryset.update(is_crm_validated=False, validation_date=None)
        self.message_user(request, f'{updated} CRM(s) invalidado(s).')
