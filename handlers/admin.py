from django.contrib import admin
from .models import Product, Category, BotSettings

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category')
    search_fields = ('name', 'category__name')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class BotSettingsAdmin(admin.ModelAdmin):
    list_display = ('setting_name', 'setting_value')
    search_fields = ('setting_name',)

admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(BotSettings, BotSettingsAdmin)