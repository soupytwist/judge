from django.contrib import admin
from judge import models

class ContestAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'begin_at', 'end_at', 'description'),
        },),
        ('Advanced Options', {
            'classes': ('collapse',),
            'fields': ('contestants',),
        },),
    )

class ProblemPartAdmin(admin.TabularInline):
    model = models.ProblemPart

class ProblemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    inlines = [
        ProblemPartAdmin,
    ]

admin.site.register(models.Contest, ContestAdmin)
admin.site.register(models.Problem, ProblemAdmin)
