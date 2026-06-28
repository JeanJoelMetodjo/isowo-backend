from rest_framework import serializers
from .models import Categorie


class CategorieSerializer(serializers.ModelSerializer):
    nombre_produits = serializers.SerializerMethodField()

    class Meta:
        model = Categorie
        fields = ["id", "nom", "description", "nombre_produits", "date_creation"]
        read_only_fields = ["id", "date_creation"]

    def get_nombre_produits(self, obj):
        return obj.produits.count()