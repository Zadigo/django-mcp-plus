from django.contrib import admin

from bird_counter.models import Bird, City, Location


@admin.register(Bird)
class BirdAdmin(admin.ModelAdmin):
    list_display = ('species', 'location', 'count')
    search_fields = ('species',)
    ordering = ('species',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    search_fields = ('name',)
    ordering = ('name',)
