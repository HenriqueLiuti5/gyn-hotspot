from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Radacct, Radcheck, Radpostauth, Userinfo
from .serializers import (
    DashboardSerializer,
    RadacctSerializer,
    RadpostAuthSerializer,
    RegisteredUserSerializer,
    UserinfoSerializer,
)


# ─────────────────────────────────────────
# Paginação padrão do sistema
# ─────────────────────────────────────────

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ─────────────────────────────────────────
# Autenticação
# ─────────────────────────────────────────

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Informe usuário e senha.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'error': 'Credenciais inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        return Response({
            'message': 'Login realizado com sucesso.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout realizado.'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        })


# ─────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        today = timezone.now().date()

        active_sessions = Radacct.objects.filter(acctstoptime__isnull=True).count()
        total_users = Userinfo.objects.count()

        auth_hoje = Radpostauth.objects.filter(authdate__date=today)
        auth_attempts_today = auth_hoje.count()
        auth_success_today = auth_hoje.filter(reply='Access-Accept').count()
        auth_failure_today = auth_hoje.filter(reply='Access-Reject').count()

        data = {
            'active_sessions': active_sessions,
            'total_users': total_users,
            'auth_attempts_today': auth_attempts_today,
            'auth_success_today': auth_success_today,
            'auth_failure_today': auth_failure_today,
        }
        serializer = DashboardSerializer(data)
        return Response(serializer.data)


# ─────────────────────────────────────────
# Sessões Ativas
# ─────────────────────────────────────────

class ActiveSessionsView(generics.ListAPIView):
    """
    Retorna sessões ativas (acctstoptime IS NULL).
    Suporta filtro por ?username=
    """
    serializer_class = RadacctSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Radacct.objects.filter(acctstoptime__isnull=True).order_by('-acctstarttime')
        username = self.request.query_params.get('username')
        if username:
            qs = qs.filter(username__icontains=username)
        return qs


# ─────────────────────────────────────────
# Histórico de Autenticação
# ─────────────────────────────────────────

class AuthHistoryView(generics.ListAPIView):
    """
    Histórico de tentativas de autenticação.
    Filtros disponíveis:
      ?username=     → filtra por usuário
      ?reply=        → Access-Accept | Access-Reject
      ?date_from=    → YYYY-MM-DD
      ?date_to=      → YYYY-MM-DD
    """
    serializer_class = RadpostAuthSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Radpostauth.objects.all().order_by('-authdate')

        username = self.request.query_params.get('username')
        reply = self.request.query_params.get('reply')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if username:
            qs = qs.filter(username__icontains=username)
        if reply:
            qs = qs.filter(reply=reply)
        if date_from:
            qs = qs.filter(authdate__date__gte=date_from)
        if date_to:
            qs = qs.filter(authdate__date__lte=date_to)

        return qs


# ─────────────────────────────────────────
# Usuários Registrados
# ─────────────────────────────────────────

class RegisteredUsersView(APIView):
    """
    Lista usuários com info completa (Userinfo + Radcheck).
    Filtro: ?username=
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    pagination_class = StandardPagination

    def get(self, request):
        username_filter = request.query_params.get('username', '').strip()

        userinfo_qs = Userinfo.objects.all()
        if username_filter:
            userinfo_qs = userinfo_qs.filter(username__icontains=username_filter)

        # Usuários que têm senha cadastrada no Radcheck
        usernames_with_password = set(
            Radcheck.objects.values_list('username', flat=True)
        )

        # Paginação manual
        paginator = StandardPagination()
        page = paginator.paginate_queryset(userinfo_qs, request)

        result = [
            {
                'username': u.username,
                'firstname': u.firstname,
                'lastname': u.lastname,
                'cpf': u.cpf,
                'has_password': u.username in usernames_with_password,
            }
            for u in page
        ]

        serializer = RegisteredUserSerializer(result, many=True)
        return paginator.get_paginated_response(serializer.data)


class RegisteredUserDetailView(APIView):
    """
    Detalhe de um usuário: info + histórico de sessões + últimas autenticações.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(self, request, username):
        try:
            userinfo = Userinfo.objects.get(username=username)
        except Userinfo.DoesNotExist:
            return Response({'error': 'Usuário não encontrado.'}, status=404)

        sessions = Radacct.objects.filter(username=username).order_by('-acctstarttime')[:10]
        auth_logs = Radpostauth.objects.filter(username=username).order_by('-authdate')[:10]

        return Response({
            'info': UserinfoSerializer(userinfo).data,
            'recent_sessions': RadacctSerializer(sessions, many=True).data,
            'recent_auth': RadpostAuthSerializer(auth_logs, many=True).data,
        })