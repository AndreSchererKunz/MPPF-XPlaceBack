from django.contrib.auth.models import AbstractUser # Permite criar um modelo de usuário customizado com os mesmos campos e comportamentos padrão do Django.
from django.db import models

class CustomUser(AbstractUser): # Herda todos os campos de User padrão do Django, mas permite extensão com campos personalizados.
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following') #symmetrical=False: significa que seguir alguém não implica ser seguido de volta. related_name='following': permite acessar os usuários que este usuário segue.
    groups = models.ManyToManyField('auth.Group',related_name="customuser_set",blank=True)
    user_permissions = models.ManyToManyField('auth.Permission',related_name="customuser_set",blank=True)
    avatar = models.ImageField(upload_to="avatars/", default="avatars/default1.png", blank=True, null=True) # upload_to="avatars/": salva os arquivos enviados na pasta avatars/.

    def __str__(self):
        return self.username

class Post(models.Model): # Representa uma publicação feita por um usuário.
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="posts") # Cada post pertence a um CustomUser.
    content = models.TextField(max_length=280, blank=True, null=True) # Post ou repost
    created_at = models.DateTimeField(auto_now_add=True) # Data/hora automática de criação do post.
    likes = models.ManyToManyField(CustomUser, related_name="liked_posts", blank=True) # Lista de usuários que curtiram este post.
    bookmark = models.ManyToManyField(CustomUser, related_name="bookmarked_posts", blank=True) # Lista de usuários que salvaram (favoritaram) o post.
    repost = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="reposts") # Repost aponta para outro post. Permite cadeia de reposts (ex: repost de repost).

    def __str__(self):
        try:
            if self.repost:
                username = self.repost.user.username if self.repost.user else "usuário desconhecido"
                content = self.repost.content[:50] if self.repost.content else ""
                return f"{self.user.username} reposted: {username} - {content}"
        except Exception:
            return f"{self.user.username} reposted: conteúdo indisponível"
        return f"{self.user.username}: {self.content[:50] if self.content else ''}"
        # Este método define como o post será exibido como string:
        # Se for um repost, mostra o nome do autor original e trecho do conteúdo.
        # Se não, mostra os primeiros 50 caracteres do conteúdo.
