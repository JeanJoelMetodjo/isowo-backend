from rest_framework import serializers
from .models import PaiementClient
from ventes.models import Vente
from ventes.utils import creer_version_facture


class PaiementClientSerializer(serializers.ModelSerializer):
    vente_reference = serializers.CharField(source="vente.reference", read_only=True)
    client_nom = serializers.CharField(source="client.nom_complet", read_only=True)
    utilisateur_nom = serializers.CharField(source="utilisateur.username", read_only=True)

    class Meta:
        model = PaiementClient
        fields = [
            "id", "vente", "vente_reference", "client", "client_nom",
            "utilisateur", "utilisateur_nom", "montant", "notes", "date"
        ]
        read_only_fields = ["id", "client", "utilisateur", "date"]


class PaiementClientCreateSerializer(serializers.Serializer):
    vente = serializers.IntegerField()
    montant = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        try:
            vente = Vente.objects.get(pk=attrs["vente"])
        except Vente.DoesNotExist:
            raise serializers.ValidationError({"vente": "Vente introuvable."})

        if vente.statut == "annulee":
            raise serializers.ValidationError({"vente": "Impossible de payer une vente annulée."})

        if vente.statut == "validee" and vente.solde_restant <= 0:
            raise serializers.ValidationError({"vente": "Cette vente est déjà soldée."})

        if attrs["montant"] <= 0:
            raise serializers.ValidationError({"montant": "Le montant doit être supérieur à 0."})

        if attrs["montant"] > vente.solde_restant:
            raise serializers.ValidationError({
                "montant": f"Le montant ({attrs['montant']}) dépasse le solde restant ({vente.solde_restant})."
            })

        attrs["_vente"] = vente
        return attrs

    def create(self, validated_data):
        vente = validated_data["_vente"]
        montant = validated_data["montant"]
        utilisateur = self.context["request"].user

        paiement = PaiementClient.objects.create(
            vente=vente,
            client=vente.client,
            utilisateur=utilisateur,
            montant=montant,
            notes=validated_data.get("notes", ""),
        )

        # Recalculer les totaux de la vente
        vente.calculer_totaux()
        creer_version_facture(
            vente=vente,
            motif=f"Paiement de {montant} {vente.client.nom_complet}",
            utilisateur=self.context["request"].user,
        )

        return paiement