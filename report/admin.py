from django.contrib import admin
from .models import Report, ReportCategory, ReportAttachment


@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'scope', 'is_active', 'created_at')
    list_filter = ('scope', 'is_active')
    search_fields = ('name',)


class ReportAttachmentInline(admin.TabularInline):
    model = ReportAttachment
    extra = 0


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'target_type', 'target_user', 'target_property', 'category', 'status', 'created_at')
    list_filter = ('target_type', 'status', 'category')
    search_fields = ('title', 'description', 'reporter__username')
    inlines = [ReportAttachmentInline]

