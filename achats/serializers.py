from rest_framework import serializers
from django.db import transaction
from .models import AchatFournisseur, LigneAchat, PaiementFournisseur
from fournisseurs.models import Fournisseur
from produits.models import Produit


class LigneAchatSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source="produit.nom", read_only=True)
    produit_code = serializers.CharField(source="produit.code", read_only=True)

    class Meta:
        model = LigneAchat
        fields = [
            "id", "produit", "produit_nom", "produit_code",
            "quantite", "prix_unitaire", "prix_total"
        ]
        read_only_fields = ["id", "prix_total"]


class LigneAchatCreateSerializer(serializers.Serializer):
    produit = serializers.IntegerField()
    quantite = serializers.IntegerField(min_value=1)
    prix_unitaire = serializers.DecimalField(max_digits=12, decimal_places=2)


class AchatFournisseurSerializer(serializers.ModelSerializer):
    lignes = LigneAchatSerializer(many=True, read_only=True)
    fournisseur_nom = serializers.CharField(
        source="fournisseur.nom_entreprise", read_only=True
    )
    utilisateur_nom = serializers.CharField(
        source="utilisateur.username", read_only=True
    )

    class Meta:
        model = AchatFournisseur
        fields = [
            "id", "reference", "fournisseur", "fournisseur_nom",
            "utilisateur", "utilisateur_nom", "montant_total",
            "montant_paye", "solde_restant", "statut", "notes",
            "lignes", "date", "date_modification"
        ]
        read_only_fields = [
            "id", "reference", "montant_total", "montant_paye",
            "solde_restant", "statut", "date", "date_modification"
        ]


class AchatCreateSerializer(serializers.Serializer):
    fournisseur = serializers.IntegerField()
    lignes = LigneAchatCreateSerializer(many=True, min_length=1)
    montant_paye = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        try:
            Fournisseur.objects.get(pk=attrs["fournisseur"])
        except Fournisseur.DoesNotExist:
            raise serializers.ValidationError({"fournisseur": "Fournisseur introuvable."})

        for ligne in attrs["lignes"]:
            try:
                Produit.objects.get(pk=ligne["produit"])
            except Produit.DoesNotExist:
                raise serializers.ValidationError(
                    {"lignes": f"Produit ID {ligne['produit']} introuvable."}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        from stock.utils import ajuster_stock

        fournisseur = Fournisseur.objects.get(pk=validated_data["fournisseur"])
        montant_paye = validated_data["montant_paye"]

        achat = AchatFournisseur.objects.create(
            fournisseur=fournisseur,
            utilisateur=self.context["request"].user,
            notes=validated_data.get("notes", ""),
            montant_paye=montant_paye,
        )

        montant_total = 0
        for ligne_data in validated_data["lignes"]:
            produit = Produit.objects.get(pk=ligne_data["produit"])
            ligne = LigneAchat.objects.create(
                achat=achat,
                produit=produit,
                quantite=ligne_data["quantite"],
                prix_unitaire=ligne_data["prix_unitaire"],
            )
            montant_total += ligne.prix_total

            # Entrée stock
            ajuster_stock(
                produit=produit,
                quantite=ligne_data["quantite"],
                type_mouvement="entree",
                motif=f"Achat {achat.reference}",
                reference=achat.reference,
            )

        achat.montant_total = montant_total
        achat.solde_restant = montant_total - montant_paye
        if achat.solde_restant <= 0:
            achat.solde_restant = 0
            achat.statut = "valide"
        else:
            achat.statut = "partiel"
        achat.save()

        # Paiement initial si > 0
        if montant_paye > 0:
            PaiementFournisseur.objects.create(
                achat=achat,
                fournisseur=fournisseur,
                utilisateur=self.context["request"].user,
                montant=montant_paye,
                notes="Paiement initial",
            )

        return achat


class PaiementFournisseurSerializer(serializers.ModelSerializer):
    achat_reference = serializers.CharField(source="achat.reference", read_only=True)
    fournisseur_nom = serializers.CharField(
        source="fournisseur.nom_entreprise", read_only=True
    )
    utilisateur_nom = serializers.CharField(
        source="utilisateur.username", read_only=True
    )

    class Meta:
        model = PaiementFournisseur
        fields = [
            "id", "achat", "achat_reference", "fournisseur",
            "fournisseur_nom", "utilisateur", "utilisateur_nom",
            "montant", "notes", "date"
        ]
        read_only_fields = ["id", "fournisseur", "utilisateur", "date"]


class PaiementFournisseurCreateSerializer(serializers.Serializer):
    achat = serializers.IntegerField()
    montant = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        try:
            achat = AchatFournisseur.objects.get(pk=attrs["achat"])
        except AchatFournisseur.DoesNotExist:
            raise serializers.ValidationError({"achat": "Achat introuvable."})

        if achat.statut == "annule":
            raise serializers.ValidationError({"achat": "Impossible de payer un achat annulé."})

        if achat.solde_restant <= 0:
            raise serializers.ValidationError({"achat": "Cet achat est déjà soldé."})

        if attrs["montant"] <= 0:
            raise serializers.ValidationError({"montant": "Le montant doit être supérieur à 0."})

        if attrs["montant"] > achat.solde_restant:
            raise serializers.ValidationError({
                "montant": f"Le montant ({attrs['montant']}) dépasse le solde restant ({achat.solde_restant})."
            })

        attrs["_achat"] = achat
        return attrs

    def create(self, validated_data):
        achat = validated_data["_achat"]
        paiement = PaiementFournisseur.objects.create(
            achat=achat,
            fournisseur=achat.fournisseur,
            utilisateur=self.context["request"].user,
            montant=validated_data["montant"],
            notes=validated_data.get("notes", ""),
        )
        achat.calculer_totaux()
        return paiement