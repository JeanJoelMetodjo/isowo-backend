from rest_framework import serializers
from .models import Produit
from categories.serializers import CategorieSerializer
from fournisseurs.serializers import FournisseurSerializer


class ProduitSerializer(serializers.ModelSerializer):
    categorie_detail = CategorieSerializer(source="categorie", read_only=True)
    fournisseur_detail = FournisseurSerializer(source="fournisseur", read_only=True)
    quantite_stock = serializers.ReadOnlyField()
    en_alerte = serializers.ReadOnlyField()

    class Meta:
        model = Produit
        fields = [
            "id", "code", "nom", "marque", "description", "couleur",
            "poids_volume", "categorie", "categorie_detail", "fournisseur",
            "fournisseur_detail", "prix_achat", "prix_vente", "seuil_alerte",
            "est_actif", "quantite_stock", "en_alerte",
            "date_creation", "date_modification"
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class ProduitCreateUpdateSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Produit
        fields = [
            "id", "code", "nom", "marque", "description", "couleur",
            "poids_volume", "categorie", "fournisseur", "prix_achat",
            "prix_vente", "seuil_alerte", "est_actif"
        ]

    def validate_code(self, value):
        if not value:
            # Générer un code automatique
            from django.utils import timezone
            annee = timezone.now().year
            dernier = Produit.objects.filter(
                code__startswith=f"PRD-{annee}-"
            ).order_by("-code").first()
            if dernier:
                try:
                    numero = int(dernier.code.split("-")[-1]) + 1
                except ValueError:
                    numero = 1
            else:
                numero = 1
            return f"PRD-{annee}-{numero:03d}"
        return value

    def create(self, validated_data):
        from stock.models import Stock
        produit = Produit.objects.create(**validated_data)
        Stock.objects.create(produit=produit, quantite=0)
        return produit