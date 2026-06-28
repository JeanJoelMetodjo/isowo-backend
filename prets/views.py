from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from historique.utils import enregistrer_action
from .models import PretMarchandise, RemboursementMarchandise, PretArgent, RemboursementArgent
from .serializers import (
    PretMarchandiseSerializer, PretMarchandiseCreateSerializer,
    RemboursementMarchandiseCreateSerializer,
    PretArgentSerializer, PretArgentCreateSerializer,
    RemboursementArgentCreateSerializer,
)


# ─── Prêts Marchandises ───────────────────────────────────────────

class PretMarchandiseListCreateView(generics.ListAPIView):
    serializer_class = PretMarchandiseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PretMarchandise.objects.select_related(
            "produit", "utilisateur"
        ).prefetch_related("remboursements").all()
        statut = self.request.query_params.get("statut")
        if statut:
            queryset = queryset.filter(statut=statut)
        return queryset


class PretMarchandiseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PretMarchandiseCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            pret = serializer.create(serializer.validated_data)
            enregistrer_action(
                utilisateur=request.user,
                type_action="creation",
                module="prets",
                reference=pret.reference,
                description=f"Prêt marchandise {pret.reference} créé.",
                request=request,
            )
            return Response(
                PretMarchandiseSerializer(pret).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PretMarchandiseDetailView(generics.RetrieveAPIView):
    queryset = PretMarchandise.objects.select_related(
        "produit", "utilisateur"
    ).prefetch_related("remboursements").all()
    serializer_class = PretMarchandiseSerializer
    permission_classes = [IsAuthenticated]


class RemboursementMarchandiseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            pret = PretMarchandise.objects.get(pk=pk)
        except PretMarchandise.DoesNotExist:
            return Response({"detail": "Prêt introuvable."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RemboursementMarchandiseCreateSerializer(
            data=request.data,
            context={"request": request, "pret": pret}
        )
        if serializer.is_valid():
            remboursement = serializer.create(serializer.validated_data)
            enregistrer_action(
                utilisateur=request.user,
                type_action="remboursement",
                module="prets",
                reference=pret.reference,
                description=f"Remboursement marchandise pour le prêt {pret.reference}.",
                request=request,
            )
            return Response(
                PretMarchandiseSerializer(pret).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── Prêts Argent ─────────────────────────────────────────────────

class PretArgentListCreateView(generics.ListAPIView):
    serializer_class = PretArgentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PretArgent.objects.select_related(
            "utilisateur"
        ).prefetch_related("remboursements").all()
        statut = self.request.query_params.get("statut")
        if statut:
            queryset = queryset.filter(statut=statut)
        return queryset


class PretArgentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PretArgentCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            pret = serializer.create(serializer.validated_data)
            enregistrer_action(
                utilisateur=request.user,
                type_action="creation",
                module="prets",
                reference=pret.reference,
                description=f"Prêt argent {pret.reference} créé.",
                request=request,
            )
            return Response(
                PretArgentSerializer(pret).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PretArgentDetailView(generics.RetrieveAPIView):
    queryset = PretArgent.objects.select_related(
        "utilisateur"
    ).prefetch_related("remboursements").all()
    serializer_class = PretArgentSerializer
    permission_classes = [IsAuthenticated]


class RemboursementArgentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            pret = PretArgent.objects.get(pk=pk)
        except PretArgent.DoesNotExist:
            return Response({"detail": "Prêt introuvable."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RemboursementArgentCreateSerializer(
            data=request.data,
            context={"request": request, "pret": pret}
        )
        if serializer.is_valid():
            serializer.create(serializer.validated_data)
            enregistrer_action(
                utilisateur=request.user,
                type_action="remboursement",
                module="prets",
                reference=pret.reference,
                description=f"Remboursement argent pour le prêt {pret.reference}.",
                request=request,
            )
            return Response(
                PretArgentSerializer(pret).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)