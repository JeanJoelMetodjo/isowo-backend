from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from historique.utils import enregistrer_action
from .models import Stock, MouvementStock
from .serializers import StockSerializer, MouvementStockSerializer, AjustementManuelSerializer
from .utils import ajuster_stock
from produits.models import Produit
from authentification.permissions import EstAdmin


class StockListView(generics.ListAPIView):
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Stock.objects.select_related("produit__categorie").all()


class MouvementStockListView(generics.ListAPIView):
    serializer_class = MouvementStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = MouvementStock.objects.select_related("produit").all()
        produit_id = self.request.query_params.get("produit")
        type_mouvement = self.request.query_params.get("type")
        if produit_id:
            queryset = queryset.filter(produit_id=produit_id)
        if type_mouvement:
            queryset = queryset.filter(type=type_mouvement)
        return queryset


class AjustementManuelView(APIView):
    permission_classes = [EstAdmin]

    def post(self, request):
        serializer = AjustementManuelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            produit = Produit.objects.get(pk=serializer.validated_data["produit"])
        except Produit.DoesNotExist:
            return Response({"detail": "Produit introuvable."}, status=status.HTTP_404_NOT_FOUND)

        quantite = serializer.validated_data["quantite"]
        motif = serializer.validated_data["motif"]

        stock = ajuster_stock(
            produit=produit,
            quantite=quantite,
            type_mouvement="ajustement",
            motif=motif,
        )

        enregistrer_action(
            utilisateur=request.user,
            type_action="ajustement",
            module="stock",
            reference=str(produit.code or produit.nom),
            description=f"Ajustement manuel : {motif} ({quantite}).",
            request=request,
        )

        return Response({
            "detail": "Ajustement effectué.",
            "quantite_actuelle": stock.quantite
        })