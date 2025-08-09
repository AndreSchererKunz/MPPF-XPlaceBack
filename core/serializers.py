from rest_framework import serializers
from .models import CustomUser, Post

class UserSerializer(serializers.ModelSerializer): # Serializador principal para listar/exibir perfis de usuários.
    # Conta a quantidade de seguidores, seguindo e posts para cada usuário.
    followers_count = serializers.IntegerField(source='followers.count', read_only=True)
    following_count = serializers.IntegerField(source='following.count', read_only=True)
    posts_count = serializers.IntegerField(source='posts.count', read_only=True)

    # Campos calculados manualmente por métodos get_avatar e get_name.
    avatar = serializers.SerializerMethodField() 
    name = serializers.SerializerMethodField()

    class Meta: # Define os campos a serem retornados na API de usuário.
        model = CustomUser
        fields = ['id', 'name','username', 'email', 'posts_count','followers_count', 'following_count', 'avatar']

    def get_avatar(self,obj):   # Retorna o URL absoluto do avatar
        request = self.context.get("request")

        if obj.avatar:
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url 
        return None 
    
    def get_name(self, obj):    # Concatena nome e sobrenome para formar o nome completo.
        first_name = obj.first_name or ""
        last_name = obj.last_name or ""

        return f"{first_name} {last_name}".strip()

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'avatar']  # Só permite editar nome, sobrenome, nome de usuário e avatar.

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)   # Define o campo password como somente de escrita, para não ser exibido no retorno.
    first_name = serializers.CharField(required=True, allow_blank=False)
    last_name = serializers.CharField(required=True, allow_blank=False)

    class Meta: # Campos obrigatórios para registrar um novo usuário.
        model = CustomUser
        fields = ["username", "email", "password", "first_name", "last_name", "avatar"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user
    # Remove a senha do dicionário original.
    # Cria o usuário e aplica set_password, que faz o hash corretamente.

class PostSerializer(serializers.ModelSerializer):  # Serializador completo para exibir e criar postagens.
    repost = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    name = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    bookmark = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    is_reposted = serializers.SerializerMethodField()

    class Meta: # Lista completa dos campos que serão expostos na API de post.
        model = Post
        fields = ['id', 'user', 'name', 'username', 'user_avatar', 'content', 'created_at', 'likes', 'bookmark', 'repost','is_liked', 'is_bookmarked', 'is_reposted'  ]

    def create(self, validated_data):   # Garante que o post seja associado ao usuário autenticado. Não aceita user como input do cliente.
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    # Métodos auxiliares
    def get_name(self, obj):
        first_name = obj.user.first_name or ""
        last_name = obj.user.last_name or ""
        return f"{first_name} {last_name}".strip()
    
    def get_user_avatar(self,obj):
        if obj.user.avatar:
            return self.context['request'].build_absolute_uri(obj.user.avatar.url)
        return self.context['request'].build_absolute_uri('/media/avatars/default1.png')  
    
    def get_created_at(self, obj):
        return obj.created_at.strftime("%d/%m/%y - %H:%M")
    
    def get_likes(self, obj):
        return obj.likes.count()
    
    def get_bookmark(self, obj):
        return obj.bookmark.count()
    
    # Retorna um mini-objeto com dados do post original (em reposts).
    def get_repost(self, obj):
        if obj.repost:
            return {
                "id": obj.repost.id,
                "username": obj.repost.user.username,
                "content": obj.repost.content,
                "created_at": obj.repost.created_at
            }

    # Verificam se o post já foi curtido, salvo ou repostado pelo usuário autenticado.
    def get_is_liked(self, obj):
        user = self.context['request'].user
        return user in obj.likes.all() if user.is_authenticated else False

    def get_is_bookmarked(self, obj):
        user = self.context['request'].user
        return user in obj.bookmark.all() if user.is_authenticated else False

    def get_is_reposted(self, obj):
        user = self.context['request'].user
        return Post.objects.filter(user=user, repost=obj).exists() if user.is_authenticated else False