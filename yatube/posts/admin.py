from django.contrib import admin

from posts.models import Post, Group, Comment, Follow


class CommentsInline(admin.TabularInline):
    model = Comment


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'created',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'
    inlines = [
        CommentsInline,
    ]


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Follow)
