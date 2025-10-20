from django.contrib import admin
from .models import File, UserStorage



class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_filename', 'file_type', 'size', 'user_id', 'uploaded_at')
    list_filter = ('user_id', 'file_type')
    search_fields = ('original_filename', 'user_id')
    ordering = ('-uploaded_at',)

admin.site.register(File, FileAdmin)

class UserStorageAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'total_storage_used', 'original_storage_used', 'last_updated')
    list_filter = ('user_id',)
    search_fields = ('user_id',)
    ordering = ('-last_updated',)

admin.site.register(UserStorage, UserStorageAdmin)