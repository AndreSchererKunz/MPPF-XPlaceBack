from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q

from django.shortcuts import get_object_or_404

from .models import CustomUser, Post
from .serializers import UserSerializer, PostSerializer, UserRegisterSerializer, UserUpdateSerializer
from django.db.models import Count

class PostPagination(PageNumberPagination): # Classe de paginação
    page_size = 10  # Número de itens por página
    page_size_query_param = 'page_size'
    max_page_size = 100  # Tamanho máximo da página

# VieSet para gerenciar usuários.
class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all() # Define o conjunto de dados base que será manipulado (todos os usuários).
    serializer_class = UserSerializer # Define o serializer padrão para transformar o modelo em JSON.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Permite leitura pública, mas só usuários autenticados podem fazer alterações (POST, PUT...).

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated]) # Cria um endpoint GET /users/me/ para obter os próprios dados e PATCH /users/me/ para atualizar.
    def me(self, request):
        user = request.user # Pega o usuário autenticado atual.

        # Se for um GET, retorna os dados do usuário logado.
        if request.method == 'GET':
            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data)

        # Se for PATCH, atualiza parcialmente os dados do usuário (ex: nome ou avatar).
        elif request.method == 'PATCH':
            serializer = UserUpdateSerializer(user, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly],  url_path='profile/(?P<username>[^/.]+)')    # Cria um endpoint GET /users/profile/<username>/.
    def profile(self, request, username=None):

        user = get_object_or_404(CustomUser, username=username) # Busca o usuário pelo nome de usuário ou retorna 404.

        # Constrói a URL absoluta do avatar.
        avatar_url = user.avatar.url if user.avatar else "/default-avatar.png"
        if user.avatar:
            avatar_url = request.build_absolute_uri(user.avatar.url)

        # Retorna um dicionário com os dados públicos do perfil e se o usuário logado segue aquele perfil.
        user_data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "avatar": avatar_url,
            "followers_count": user.followers.count(),
            "following_count": user.following.count(),
            "is_me": request.user == user,
            "is_following": request.user in user.followers.all() if request.user.is_authenticated else False
        }
        return Response(user_data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly],
            url_path='profile/(?P<username>[^/.]+)/followers')
    def followers(self, request, username=None):
        # Lista todos os seguidores de um usuário específico.
        user = get_object_or_404(CustomUser, username=username)
        followers_qs = user.followers.all()
        serializer = UserSerializer(followers_qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly],
            url_path='profile/(?P<username>[^/.]+)/following')
    def following(self, request, username=None):
        # Lista todos os usuários que um usuário específico está seguindo.
        user = get_object_or_404(CustomUser, username=username)
        following_qs = user.following.all()
        serializer = UserSerializer(following_qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
    # Cria POST /users/<id>/follow/.

        target_user = self.get_object()
        user = request.user
        # Impede seguir a si mesmo.
        if user == target_user:
            return Response({"detail": "Você não pode seguir a si mesmo."}, status=400)

        if target_user in user.following.all():
            user.following.remove(target_user)
            return Response({"detail": "Unfollowed"}, status=204)
        else:
            user.following.add(target_user)

            from notifications.utils import create_notification
            create_notification(
                recipient=target_user,
                sender=request.user,
                type='FOLLOW',
                message=f'{request.user.username} começou a seguir você  '
            )

        return Response({"detail": "Followed"}, status=201)

# Lista os posts mais curtidos.
class MostLikedPostsViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.annotate(like_count=Count('likes')).order_by('-like_count')[:4]
    serializer_class = PostSerializer

# Lista perfis aleatórios.
class RandomFollowersViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.order_by("?")[:4]
    serializer_class = UserSerializer

# View para cadastro de novo usuário. Usa o UserRegisterSerializer e retorna os dados do novo usuário após salvar.
class UserRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_data = UserSerializer(user, context={'request': request}).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ViewSet completo para posts.
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PostPagination 

    # Ao criar um post, associa automaticamente ao usuário autenticado.
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


    @action(detail=False, methods=['get'], url_path='feed', permission_classes=[IsAuthenticated])
    def feed(self, request):
        # Cria GET /posts/feed/ — mostra posts do usuário logado + de quem ele segue.

        # Filtra posts de user + user.following.
        user = request.user
        following = user.following.all()
        posts = Post.objects.filter(Q(user__in=[*following, user])).order_by('-created_at')

        # Aplica paginação e retorna resposta paginada.
        paginator = PostPagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = self.get_serializer(paginated_posts, many=True)
        return paginator.get_paginated_response(serializer.data)


    @action(detail=False, methods=['get'], url_path='user/(?P<username>[^/.]+)')
    def posts_by_user(self, request, username=None):
        user = get_object_or_404(CustomUser, username=username)
        posts = Post.objects.filter(user=user).order_by('-created_at')
        # Retorna todos os posts criados por um usuário específico.

        # Aplica paginação e retorna resposta paginada.
        paginator = PostPagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = self.get_serializer(paginated_posts, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='bookmark', permission_classes=[IsAuthenticated])
    def bookmarked_posts(self, request):
        user = request.user
        posts = user.bookmarked_posts.all()
        # Retorna os posts salvos pelo usuário atual.

        # Paginação
        paginator = PostPagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = self.get_serializer(paginated_posts, many=True)
        return paginator.get_paginated_response(serializer.data)

    # Curtidas: adiciona ou remove o like do post com pk.
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        if request.user in post.likes.all():
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)

            from notifications.utils import create_notification
            create_notification(
                recipient=post.user,
                sender=request.user,
                type='LIKE',
                post=post,
                message=f'{request.user.username} curtiu seu post  '
            )

        return Response(status=204)

    # Favoritos: salva ou remove post dos bookmarks.
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def bookmark(self, request, pk=None):
        post = self.get_object()
        if request.user in post.bookmark.all():
            post.bookmark.remove(request.user)
        else:
            post.bookmark.add(request.user)

            from notifications.utils import create_notification
            create_notification(
                recipient=post.user,
                sender=request.user,
                type='BOOKMARK',
                post=post,
                message=f'{request.user.username} salvou seu post  '
            )

        return Response(status=204)

    # Repost: cria ou desfaz repost de um post existente.
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def repost(self, request, pk=None):
        original_post = self.get_object()
        repost_instance = Post.objects.filter(user=request.user, repost=original_post).first()

        if repost_instance:
            repost_instance.delete()
            return Response({"detail": "Repost removed"}, status=204)

        Post.objects.create(user=request.user, repost=original_post)

        from notifications.utils import create_notification
        create_notification(
            recipient=original_post.user,
            sender=request.user,
            type='REPOST',
            post=original_post,
            message=f'{request.user.username} repostou seu post  '
        )

        return Response({"detail": "Repost created"}, status=201)