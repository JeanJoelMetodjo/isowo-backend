from rest_framework import serializers
from .models import HistoriqueAction


class HistoriqueActionSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(
        source="utilisateur.username", read_only=True
    )

    class Meta:
        model = HistoriqueAction
        fields = [
            "id", "utilisateur", "utilisateur_nom", "type_action",
            "module", "reference", "description", "donnees_avant",
            "donnees_apres", "adresse_ip", "date"
        ]
        read_only_fields = fields