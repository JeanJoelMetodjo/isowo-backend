from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from historique.utils import enregistrer_action
from .models import PaiementClient
from .serializers import PaiementClientSerializer, PaiementClientCreateSerializer
from authentification.permissions import EstAdmin


class PaiementClientListCreateView(generics.ListAPIView):
    serializer_class = PaiementClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PaiementClient.objects.select_related(
            "vente", "client", "utilisateur"
        ).all()

        client = self.request.query_params.get("client")
        vente = self.request.query_params.get("vente")

        if client:
            queryset = queryset.filter(client_id=client)
        if vente:
            queryset = queryset.filter(vente_id=vente)

        return queryset


class PaiementClientCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaiementClientCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            paiement = serializer.create(serializer.validated_data)
            enregistrer_action(
                utilisateur=request.user,
                type_action="creation",
                module="paiements",
                reference=paiement.vente.reference,
                description=f"Paiement client de {paiement.montant} FCFA pour la vente {paiement.vente.reference}.",
                request=request,
            )
            return Response(
                PaiementClientSerializer(paiement).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaiementClientDeleteView(APIView):
    permission_classes = [EstAdmin]

    def delete(self, request, pk):
        try:
            paiement = PaiementClient.objects.select_related("vente").get(pk=pk)
        except PaiementClient.DoesNotExist:
            return Response(
                {"detail": "Paiement introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        vente = paiement.vente
        reference = paiement.vente.reference
        paiement.delete()

        # Recalculer les totaux après suppression
        vente.calculer_totaux()
        enregistrer_action(
            utilisateur=request.user,
            type_action="suppression",
            module="paiements",
            reference=reference,
            description=f"Paiement client supprimé pour la vente {reference}.",
            request=request,
        )
        return Response({"detail": "Paiement supprimé."}, status=status.HTTP_204_NO_CONTENT)


class VentesEnCours(generics.ListAPIView):
    """Liste des ventes avec solde restant > 0 (dettes clients)."""
    serializer_class = PaiementClientSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ventes.models import Vente
        from ventes.serializers import VenteSerializer
        ventes = Vente.objects.filter(
            statut="partielle"
        ).select_related("client").prefetch_related("lignes", "paiements").order_by("-date")

        search = request.query_params.get("search")
        if search:
            ventes = ventes.filter(
                Q(client__nom__icontains=search) |
                Q(client__prenom__icontains=search) |
                Q(reference__icontains=search)
            )

        return Response(VenteSerializer(ventes, many=True).data)