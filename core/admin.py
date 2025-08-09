from django.contrib import admin  # Permite registrar e personalizar modelos no painel administrativo.
from django.contrib.auth.admin import UserAdmin # UserAdmin é a classe base que o Django usa para exibir usuários no admin.
from django.utils.html import format_html # Serve para renderizar HTML com segurança.

from .models import CustomUser, Post

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_active", "is_staff", "avatar") # Define as colunas visíveis na lista de usuários no admin.
    search_fields = ("username", "email") # Permite buscar usuários pelo nome de usuário ou e-mail.
    list_filter = ("is_active", "is_staff") # Adiciona filtros laterais por status ativo e se é staff (admin).

    readonly_fields = ("avatar_preview",) # Torna o campo avatar_preview somente leitura (exibição visual, sem edição).

    fieldsets = UserAdmin.fieldsets + (
        ("Perfil Personalizado", {
            "fields": ("avatar", "avatar_preview", "followers")
        }),
    )
    # Adiciona uma nova seção “Perfil Personalizado” no formulário de edição de usuários, com:
    # avatar: imagem do perfil
    # avatar_preview: visualização da imagem
    # followers: campo de seguidores

    filter_horizontal = ("followers", "groups", "user_permissions") # Muda a UI para esses campos de muitos-para-muitos, facilitando a seleção.
    
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%;"/>', obj.avatar.url)
        return "(Sem imagem)"
    # Retorna uma tag <img> com o avatar renderizado no admin. Se não houver avatar, exibe texto.

    avatar_preview.short_description = "Prévia do Avatar" # Define o nome visível para o campo no admin.

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):  # Registra o modelo Post com personalização da interface.
    list_display = ("user", "content", "created_at") # Exibe o autor, conteúdo e data de criação na listagem de posts.
    search_fields = ("content", "username") # Habilita busca por conteúdo do post e nome de usuário
    list_filter = ("created_at",) # Permite filtrar posts por data de criação no admin.