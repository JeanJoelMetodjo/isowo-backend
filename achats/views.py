from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from historique.utils import enregistrer_action
from .models import AchatFournisseur, PaiementFournisseur
from .serializers import (
    AchatFournisseurSerializer,
    AchatCreateSerializer,
    PaiementFournisseurSerializer,
    PaiementFournisseurCreateSerializer,
)
from authentification.permissions import EstAdmin


class AchatListCreateView(generics.ListAPIView):
    serializer_class = AchatFournisseurSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AchatFournisseur.objects.select_related(
            "fournisseur", "utilisateur"
        ).prefetch_related("lignes__produit").all()

        search = self.request.query_params.get("search")
        statut = self.request.query_params.get("statut")
        fournisseur = self.request.query_params.get("fournisseur")

        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search) |
                Q(fournisseur__nom_entreprise__icontains=search)
            )
        if statut:
            queryset = queryset.filter(statut=statut)
        if fournisseur:
            queryset = queryset.filter(fournisseur_id=fournisseur)

        return queryset


class AchatCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AchatCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            achat = serializer.create(serializer.validated_data)
            enregistrer_action(
                utilisateur=request.user,
                type_action="creation",
                module="achats",
                reference=achat.reference,
                description=f"Achat {achat.reference} créé pour {achat.fournisseur.nom_entreprise}.",
                request=request,
            )
            return Response(
                AchatFournisseurSerializer(achat).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AchatDetailView(generics.RetrieveAPIView):
    queryset = AchatFournisseur.objects.select_related(
        "fournisseur", "utilisateur"
    ).prefetch_related("lignes__produit", "paiements").all()
    serializer_class = AchatFournisseurSerializer
    permission_classes = [IsAuthenticated]


class AchatAnnulerView(APIView):
    permission_classes = [EstAdmin]

    def post(self, request, pk):
        try:
            achat = AchatFournisseur.objects.prefetch_related(
                "lignes__produit"
            ).get(pk=pk)
        except AchatFournisseur.DoesNotExist:
            return Response(
                {"detail": "Achat introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        if achat.statut == "annule":
            return Response(
                {"detail": "Cet achat est déjà annulé."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from stock.utils import ajuster_stock
        for ligne in achat.lignes.all():
            ajuster_stock(
                produit=ligne.produit,
                quantite=-ligne.quantite,
                type_mouvement="sortie",
                motif=f"Annulation achat {achat.reference}",
                reference=achat.reference,
            )

        achat.statut = "annule"
        achat.solde_restant = 0
        achat.save()

        enregistrer_action(
            utilisateur=request.user,
            type_action="annulation",
            module="achats",
            reference=achat.reference,
            description=f"Achat {achat.reference} annulé.",
            request=request,
        )

        return Response({"detail": f"Achat {achat.reference} annulé avec succès."})


class AchatDeleteView(APIView):
    permission_classes = [EstAdmin]

    def delete(self, request, pk):
        try:
            achat = AchatFournisseur.objects.prefetch_related(
                "lignes__produit"
            ).get(pk=pk)
        except AchatFournisseur.DoesNotExist:
            return Response(
                {"detail": "Achat introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        if achat.statut != "annule":
            from stock.utils import ajuster_stock
            for ligne in achat.lignes.all():
                ajuster_stock(
                    produit=ligne.produit,
                    quantite=-ligne.quantite,
                    type_mouvement="sortie",
                    motif=f"Suppression achat {achat.reference}",
                    reference=achat.reference,
                )

        reference = achat.reference
        achat.delete()
        enregistrer_action(
            utilisateur=request.user,
            type_action="suppression",
            module="achats",
            reference=reference,
            description=f"Achat {reference} supprimé.",
            request=request,
        )
        return Response({"detail": "Achat supprimé."}, status=status.HTTP_204_NO_CONTENT)


# --- Paiements fournisseurs ---

class PaiementFournisseurListView(generics.ListAPIView):
    serializer_class = PaiementFournisseurSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PaiementFournisseur.objects.select_related(
            "achat", "fournisseur", "utilisateur"
        ).all()

        fournisseur = self.request.query_params.get("fournisseur")
        achat = self.request.query_params.get("achat")

        if fournisseur:
            queryset = queryset.filter(fournisseur_id=fournisseur)
        if achat:
            queryset = queryset.filter(achat_id=achat)

        return queryset


class PaiementFournisseurCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaiementFournisseurCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            paiement = serializer.create(serializer.validated_data)
            enregistrer_action(
                utilisateur=request.user,
                type_action="creation",
                module="achats",
                reference=paiement.achat.reference,
                description=f"Paiement fournisseur de {paiement.montant} FCFA pour l\'achat {paiement.achat.reference}.",
                request=request,
            )
            return Response(
                PaiementFournisseurSerializer(paiement).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaiementFournisseurDeleteView(APIView):
    permission_classes = [EstAdmin]

    def delete(self, request, pk):
        try:
            paiement = PaiementFournisseur.objects.select_related("achat").get(pk=pk)
        except PaiementFournisseur.DoesNotExist:
            return Response(
                {"detail": "Paiement introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        achat = paiement.achat
        reference = paiement.achat.reference
        paiement.delete()
        achat.calculer_totaux()
        enregistrer_action(
            utilisateur=request.user,
            type_action="suppression",
            module="achats",
            reference=reference,
            description=f"Paiement fournisseur supprimé pour l\'achat {reference}.",
            request=request,
        )
        return Response({"detail": "Paiement supprimé."}, status=status.HTTP_204_NO_CONTENT)


class AchatsEnCours(generics.ListAPIView):
    """Achats avec solde restant > 0 (dettes fournisseurs)."""
    serializer_class = AchatFournisseurSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        achats = AchatFournisseur.objects.filter(
            statut="partiel"
        ).select_related("fournisseur").prefetch_related("lignes", "paiements")

        search = request.query_params.get("search")
        if search:
            achats = achats.filter(
                Q(fournisseur__nom_entreprise__icontains=search) |
                Q(reference__icontains=search)
            )

        return Response(AchatFournisseurSerializer(achats, many=True).data)