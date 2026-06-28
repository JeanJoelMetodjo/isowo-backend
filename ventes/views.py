from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from historique.utils import enregistrer_action
from .models import Vente
from .serializers import VenteSerializer, VenteCreateSerializer, VenteUpdateSerializer
from authentification.permissions import EstAdmin
from rest_framework.permissions import AllowAny

class VenteListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Vente.objects.select_related(
            "client", "utilisateur"
        ).prefetch_related("lignes__produit").all()

        search = self.request.query_params.get("search")
        statut = self.request.query_params.get("statut")
        client = self.request.query_params.get("client")

        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search) |
                Q(client__nom__icontains=search) |
                Q(client__prenom__icontains=search)
            )
        if statut:
            queryset = queryset.filter(statut=statut)
        if client:
            queryset = queryset.filter(client_id=client)

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return VenteCreateSerializer
        return VenteSerializer

    def create(self, request, *args, **kwargs):
        serializer = VenteCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            vente = serializer.create(serializer.validated_data)
            enregistrer_action(
                utilisateur=request.user,
                type_action="creation",
                module="ventes",
                reference=vente.reference,
                description=f"Vente {vente.reference} créée pour {vente.client.nom_complet}.",
                request=request,
            )
            return Response(
                VenteSerializer(vente, context={"request": request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VenteDetailView(generics.RetrieveAPIView):
    queryset = Vente.objects.select_related(
        "client", "utilisateur"
    ).prefetch_related("lignes__produit", "paiements").all()
    serializer_class = VenteSerializer
    permission_classes = [IsAuthenticated]


class VenteUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            vente = Vente.objects.get(pk=pk)
        except Vente.DoesNotExist:
            return Response({"detail": "Vente introuvable."}, status=status.HTTP_404_NOT_FOUND)

        serializer = VenteUpdateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                vente = serializer.update(vente, serializer.validated_data)
                enregistrer_action(
                    utilisateur=request.user,
                    type_action="modification",
                    module="ventes",
                    reference=vente.reference,
                    description=f"Vente {vente.reference} modifiée.",
                    request=request,
                )
                return Response(VenteSerializer(vente).data)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VenteAnnulerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            vente = Vente.objects.prefetch_related("lignes__produit").get(pk=pk)
        except Vente.DoesNotExist:
            return Response({"detail": "Vente introuvable."}, status=status.HTTP_404_NOT_FOUND)

        if vente.statut == "annulee":
            return Response(
                {"detail": "Cette vente est déjà annulée."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from stock.utils import ajuster_stock
        for ligne in vente.lignes.all():
            ajuster_stock(
                produit=ligne.produit,
                quantite=ligne.quantite,
                type_mouvement="retour_vente",
                motif=f"Annulation vente {vente.reference}",
                reference=vente.reference,
            )

        vente.statut = "annulee"
        vente.solde_restant = 0
        vente.save()

        enregistrer_action(
            utilisateur=request.user,
            type_action="annulation",
            module="ventes",
            reference=vente.reference,
            description=f"Vente {vente.reference} annulée.",
            request=request,
        )

        return Response({"detail": f"Vente {vente.reference} annulée avec succès."})


class VenteDeleteView(APIView):
    permission_classes = [EstAdmin]

    def delete(self, request, pk):
        try:
            vente = Vente.objects.prefetch_related("lignes__produit").get(pk=pk)
        except Vente.DoesNotExist:
            return Response({"detail": "Vente introuvable."}, status=status.HTTP_404_NOT_FOUND)

        if vente.statut != "annulee":
            from stock.utils import ajuster_stock
            for ligne in vente.lignes.all():
                ajuster_stock(
                    produit=ligne.produit,
                    quantite=ligne.quantite,
                    type_mouvement="retour_vente",
                    motif=f"Suppression vente {vente.reference}",
                    reference=vente.reference,
                )

        reference = vente.reference
        vente.delete()
        enregistrer_action(
            utilisateur=request.user,
            type_action="suppression",
            module="ventes",
            reference=reference,
            description=f"Vente {reference} supprimée.",
            request=request,
        )
        return Response({"detail": "Vente supprimée."}, status=status.HTTP_204_NO_CONTENT)



class VentePubliqueView(generics.RetrieveAPIView):
    """Vue publique d'une facture — accessible sans authentification."""
    serializer_class = VenteSerializer
    permission_classes = [AllowAny]
    lookup_field = "reference"

    def get_queryset(self):
        return Vente.objects.select_related(
            "client", "utilisateur"
        ).prefetch_related("lignes__produit").all()


class VenteParReferenceView(generics.RetrieveAPIView):
    """Détail d'une vente par référence — pour la page d'impression interne."""
    queryset = Vente.objects.select_related(
        "client", "utilisateur"
    ).prefetch_related("lignes__produit", "paiements").all()
    serializer_class = VenteSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "reference"