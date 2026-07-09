from django.contrib import admin

from .models import ImportRow, ImportSession

admin.site.register(ImportSession)
admin.site.register(ImportRow)
