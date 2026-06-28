from rest_framework import serializers
from django.db import transaction
from .models import (
    PretMarchandise, RemboursementMarchandise,
    PretArgent, RemboursementArgent
)
from produits.models import Produit


# ─── Prêts Marchandises ───────────────────────────────────────────

class RemboursementMarchandiseSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source="utilisateur.username", read_only=True)

    class Meta:
        model = RemboursementMarchandise
        fields = [
            "id", "quantite_rendue", "montant_paye",
            "notes", "date", "utilisateur_nom"
        ]
        read_only_fields = ["id", "date"]


class PretMarchandiseSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source="produit.nom", read_only=True)
    produit_code = serializers.CharField(source="produit.code", read_only=True)
    utilisateur_nom = serializers.CharField(source="utilisateur.username", read_only=True)
    remboursements = RemboursementMarchandiseSerializer(many=True, read_only=True)
    quantite_restante = serializers.SerializerMethodField()

    class Meta:
        model = PretMarchandise
        fields = [
            "id", "reference", "beneficiaire", "produit", "produit_nom",
            "produit_code", "quantite", "quantite_rendue", "quantite_restante",
            "mode_remboursement", "montant_equivalent", "montant_rembourse",
            "date_pret", "date_retour_prevue", "statut", "notes",
            "utilisateur_nom", "remboursements"
        ]
        read_only_fields = [
            "id", "reference", "quantite_rendue", "montant_rembourse",
            "statut", "date_pret"
        ]

    def get_quantite_restante(self, obj):
        return obj.quantite - obj.quantite_rendue


class PretMarchandiseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PretMarchandise
        fields = [
            "beneficiaire", "produit", "quantite",
            "mode_remboursement", "montant_equivalent",
            "date_retour_prevue", "notes"
        ]

    def validate(self, attrs):
        produit = attrs["produit"]
        quantite = attrs["quantite"]
        if produit.quantite_stock < quantite:
            raise serializers.ValidationError({
                "quantite": f"Stock insuffisant : demandé {quantite}, disponible {produit.quantite_stock}."
            })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        from stock.utils import ajuster_stock
        produit = validated_data["produit"]
        quantite = validated_data["quantite"]

        pret = PretMarchandise.objects.create(
            **validated_data,
            utilisateur=self.context["request"].user
        )

        ajuster_stock(
            produit=produit,
            quantite=-quantite,
            type_mouvement="pret",
            motif=f"Prêt marchandise {pret.reference}",
            reference=pret.reference,
        )
        return pret


class RemboursementMarchandiseCreateSerializer(serializers.Serializer):
    quantite_rendue = serializers.IntegerField(default=0, min_value=0)
    montant_paye = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        pret = self.context["pret"]

        if pret.statut == "rembourse":
            raise serializers.ValidationError("Ce prêt est déjà entièrement remboursé.")

        quantite_restante = pret.quantite - pret.quantite_rendue
        if attrs["quantite_rendue"] > quantite_restante:
            raise serializers.ValidationError({
                "quantite_rendue": f"Quantité restante à rendre : {quantite_restante}."
            })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        from stock.utils import ajuster_stock
        pret = self.context["pret"]

        remboursement = RemboursementMarchandise.objects.create(
            pret=pret,
            utilisateur=self.context["request"].user,
            **validated_data
        )

        # Réintégrer stock si restitution produit
        if pret.mode_remboursement == "produit" and validated_data["quantite_rendue"] > 0:
            ajuster_stock(
                produit=pret.produit,
                quantite=validated_data["quantite_rendue"],
                type_mouvement="retour_pret",
                motif=f"Retour prêt {pret.reference}",
                reference=pret.reference,
            )

        # Mettre à jour les totaux du prêt
        pret.quantite_rendue += validated_data["quantite_rendue"]
        pret.montant_rembourse += validated_data["montant_paye"]

        quantite_restante = pret.quantite - pret.quantite_rendue
        if quantite_restante <= 0:
            pret.statut = "rembourse"
        else:
            pret.statut = "partiel"
        pret.save()

        return remboursement


# ─── Prêts Argent ─────────────────────────────────────────────────

class RemboursementArgentSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source="utilisateur.username", read_only=True)

    class Meta:
        model = RemboursementArgent
        fields = ["id", "montant", "notes", "date", "utilisateur_nom"]
        read_only_fields = ["id", "date"]


class PretArgentSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source="utilisateur.username", read_only=True)
    remboursements = RemboursementArgentSerializer(many=True, read_only=True)

    class Meta:
        model = PretArgent
        fields = [
            "id", "reference", "beneficiaire", "montant",
            "montant_rembourse", "solde_restant", "date_pret",
            "date_retour_prevue", "statut", "notes",
            "utilisateur_nom", "remboursements"
        ]
        read_only_fields = [
            "id", "reference", "montant_rembourse",
            "solde_restant", "statut", "date_pret"
        ]


class PretArgentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PretArgent
        fields = ["beneficiaire", "montant", "date_retour_prevue", "notes"]

    def create(self, validated_data):
        return PretArgent.objects.create(
            **validated_data,
            utilisateur=self.context["request"].user
        )


class RemboursementArgentCreateSerializer(serializers.Serializer):
    montant = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        pret = self.context["pret"]
        if pret.statut == "rembourse":
            raise serializers.ValidationError("Ce prêt est déjà entièrement remboursé.")
        if attrs["montant"] <= 0:
            raise serializers.ValidationError({"montant": "Le montant doit être supérieur à 0."})
        if attrs["montant"] > pret.solde_restant:
            raise serializers.ValidationError({
                "montant": f"Montant dépasse le solde restant ({pret.solde_restant} FCFA)."
            })
        return attrs

    def create(self, validated_data):
        pret = self.context["pret"]
        remboursement = RemboursementArgent.objects.create(
            pret=pret,
            utilisateur=self.context["request"].user,
            **validated_data
        )
        pret.calculer_solde()
        return remboursement