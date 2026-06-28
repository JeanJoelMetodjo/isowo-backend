from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import HistoriqueAction
from .serializers import HistoriqueActionSerializer
from authentification.permissions import EstAdmin


class HistoriqueListView(generics.ListAPIView):
    serializer_class = HistoriqueActionSerializer
    permission_classes = [EstAdmin]

    def get_queryset(self):
        queryset = HistoriqueAction.objects.select_related("utilisateur").all()

        module = self.request.query_params.get("module")
        type_action = self.request.query_params.get("type_action")
        utilisateur = self.request.query_params.get("utilisateur")
        search = self.request.query_params.get("search")
        date_debut = self.request.query_params.get("date_debut")
        date_fin = self.request.query_params.get("date_fin")

        if module:
            queryset = queryset.filter(module=module)
        if type_action:
            queryset = queryset.filter(type_action=type_action)
        if utilisateur:
            queryset = queryset.filter(utilisateur_id=utilisateur)
        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search) |
                Q(description__icontains=search)
            )
        if date_debut:
            queryset = queryset.filter(date__date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__date__lte=date_fin)

        return queryset


class HistoriqueDetailView(generics.RetrieveAPIView):
    queryset = HistoriqueAction.objects.select_related("utilisateur").all()
    serializer_class = HistoriqueActionSerializer
    permission_classes = [EstAdmin]


class HistoriqueStatsView(APIView):
    """Résumé rapide des actions par module et type."""
    permission_classes = [EstAdmin]

    def get(self, request):
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta

        aujourd_hui = timezone.now().date()
        il_y_a_7_jours = aujourd_hui - timedelta(days=7)

        par_module = (
            HistoriqueAction.objects
            .values("module")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        par_type = (
            HistoriqueAction.objects
            .values("type_action")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        cette_semaine = (
            HistoriqueAction.objects
            .filter(date__date__gte=il_y_a_7_jours)
            .values("type_action")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        return Response({
            "par_module": list(par_module),
            "par_type": list(par_type),
            "cette_semaine": list(cette_semaine),
            "total": HistoriqueAction.objects.count(),
        })