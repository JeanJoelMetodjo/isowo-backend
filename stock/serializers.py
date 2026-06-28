from rest_framework import serializers
from .models import Stock, MouvementStock
from produits.serializers import ProduitSerializer


class StockSerializer(serializers.ModelSerializer):
    produit_detail = ProduitSerializer(source="produit", read_only=True)

    class Meta:
        model = Stock
        fields = ["id", "produit", "produit_detail", "quantite", "date_modification"]
        read_only_fields = ["id", "date_modification"]


class MouvementStockSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source="produit.nom", read_only=True)
    produit_code = serializers.CharField(source="produit.code", read_only=True)

    class Meta:
        model = MouvementStock
        fields = [
            "id", "produit", "produit_nom", "produit_code",
            "type", "quantite", "quantite_avant", "quantite_apres",
            "motif", "reference", "date"
        ]
        read_only_fields = ["id", "quantite_avant", "quantite_apres", "date"]


class AjustementManuelSerializer(serializers.Serializer):
    produit = serializers.IntegerField()
    quantite = serializers.IntegerField()
    motif = serializers.CharField(max_length=300)