from django.contrib import admin
from judge import models

class ContestAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

class ProblemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(models.Contest, ContestAdmin)
admin.site.register(models.Problem, ProblemAdmin)
