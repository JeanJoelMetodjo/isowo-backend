from rest_framework import serializers
from django.db import transaction
from .models import Vente, LigneVente, VersionFacture
from produits.models import Produit
from clients.serializers import ClientSerializer


class LigneVenteSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source="produit.nom", read_only=True)
    produit_code = serializers.CharField(source="produit.code", read_only=True)
    prix_effectif = serializers.ReadOnlyField()

    class Meta:
        model = LigneVente
        fields = [
            "id", "produit", "produit_nom", "produit_code",
            "quantite", "prix_unitaire", "prix_special",
            "prix_effectif", "prix_total"
        ]
        read_only_fields = ["id", "prix_total"]


class LigneVenteCreateSerializer(serializers.Serializer):
    produit = serializers.IntegerField()
    quantite = serializers.IntegerField(min_value=1)
    prix_special = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )


class VersionFactureSerializer(serializers.ModelSerializer):
    cree_par_nom = serializers.SerializerMethodField()

    class Meta:
        model = VersionFacture
        fields = [
            "id", "version", "montant_total", "montant_paye",
            "solde_restant", "statut", "motif", "date", "cree_par_nom"
        ]

    def get_cree_par_nom(self, obj):
        if not obj.cree_par:
            return "—"
        return f"{obj.cree_par.nom} {obj.cree_par.prenom}".strip()


# class VenteSerializer(serializers.ModelSerializer):
#     lignes = LigneVenteSerializer(many=True, read_only=True)
#     client_detail = ClientSerializer(source="client", read_only=True)
#     utilisateur_nom = serializers.CharField(source="utilisateur.username", read_only=True)

#     class Meta:
#         model = Vente
#         fields = [
#             "id", "reference", "client", "client_detail",
#             "utilisateur", "utilisateur_nom", "remise",
#             "montant_total", "montant_paye", "solde_restant",
#             "statut", "notes", "lignes", "date", "date_modification"
#         ]
#         read_only_fields = [
#             "id", "reference", "montant_total", "montant_paye",
#             "solde_restant", "statut", "date", "date_modification"
#         ]

class VenteSerializer(serializers.ModelSerializer):
    lignes = LigneVenteSerializer(many=True, read_only=True)
    client_detail = ClientSerializer(source="client", read_only=True)
    utilisateur_nom = serializers.SerializerMethodField()
    versions = VersionFactureSerializer(many=True, read_only=True)

    class Meta:
        model = Vente
        fields = [
            "id", "reference", "client", "client_detail",
            "utilisateur", "utilisateur_nom", "remise",
            "montant_total", "montant_paye", "solde_restant",
            "statut", "notes", "lignes", "versions", "date", "date_modification"
        ]
        read_only_fields = [
            "id", "reference", "montant_total", "montant_paye",
            "solde_restant", "statut", "date", "date_modification"
        ]

    def get_utilisateur_nom(self, obj):
        if not obj.utilisateur:
            return "—"
        return f"{obj.utilisateur.nom} {obj.utilisateur.prenom}".strip()

class VenteCreateSerializer(serializers.Serializer):
    client = serializers.IntegerField()
    lignes = LigneVenteCreateSerializer(many=True, min_length=1)
    montant_paye = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    remise = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        erreurs = []
        for ligne in attrs["lignes"]:
            try:
                produit = Produit.objects.select_related("stock").get(pk=ligne["produit"])
            except Produit.DoesNotExist:
                erreurs.append(f"Produit ID {ligne['produit']} introuvable.")
                continue
            if not produit.est_actif:
                erreurs.append(f"Le produit '{produit.nom}' est inactif.")
            stock_dispo = produit.quantite_stock
            if stock_dispo < ligne["quantite"]:
                erreurs.append(
                    f"Stock insuffisant pour '{produit.nom}' : "
                    f"demandé {ligne['quantite']}, disponible {stock_dispo}."
                )
        if erreurs:
            raise serializers.ValidationError({"stock": erreurs})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        from stock.utils import ajuster_stock
        from clients.models import Client

        client = Client.objects.get(pk=validated_data["client"])
        montant_paye = validated_data["montant_paye"]
        remise = validated_data["remise"]

        vente = Vente.objects.create(
            client=client,
            utilisateur=self.context["request"].user,
            remise=remise,
            notes=validated_data.get("notes", ""),
            montant_paye=montant_paye,
        )

        for ligne_data in validated_data["lignes"]:
            produit = Produit.objects.get(pk=ligne_data["produit"])
            LigneVente.objects.create(
                vente=vente,
                produit=produit,
                quantite=ligne_data["quantite"],
                prix_unitaire=produit.prix_vente,
                prix_special=ligne_data.get("prix_special"),
            )
            ajuster_stock(
                produit=produit,
                quantite=-ligne_data["quantite"],
                type_mouvement="sortie",
                motif=f"Vente {vente.reference}",
                reference=vente.reference,
            )

        # Calcul des totaux
        from django.db.models import Sum
        sous_total = vente.lignes.aggregate(total=Sum("prix_total"))["total"] or 0
        vente.montant_total = sous_total - remise
        vente.montant_paye = montant_paye
        vente.solde_restant = vente.montant_total - montant_paye

        if vente.solde_restant <= 0:
            vente.solde_restant = 0
            vente.statut = "validee"
        else:
            vente.statut = "partielle"

        vente.save()

        from ventes.utils import creer_version_facture

        creer_version_facture(
            vente=vente,
            motif="Création de la vente",
            utilisateur=self.context["request"].user,
        )

        # Enregistrer le paiement initial si > 0
        if montant_paye > 0:
            from paiements.models import PaiementClient
            PaiementClient.objects.create(
                vente=vente,
                client=client,
                montant=montant_paye,
                notes="Paiement initial",
            )

        return vente


class VenteUpdateSerializer(serializers.Serializer):
    lignes = LigneVenteCreateSerializer(many=True, min_length=1)
    remise = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        from stock.utils import ajuster_stock

        if instance.statut == "annulee":
            raise serializers.ValidationError("Impossible de modifier une vente annulée.")

        # Restituer le stock des anciennes lignes
        for ligne in instance.lignes.all():
            ajuster_stock(
                produit=ligne.produit,
                quantite=ligne.quantite,
                type_mouvement="retour_vente",
                motif=f"Modification vente {instance.reference}",
                reference=instance.reference,
            )

        # Supprimer les anciennes lignes
        instance.lignes.all().delete()

        # Valider le nouveau stock
        erreurs = []
        for ligne_data in validated_data["lignes"]:
            try:
                produit = Produit.objects.select_related("stock").get(pk=ligne_data["produit"])
            except Produit.DoesNotExist:
                erreurs.append(f"Produit ID {ligne_data['produit']} introuvable.")
                continue
            if produit.quantite_stock < ligne_data["quantite"]:
                erreurs.append(
                    f"Stock insuffisant pour '{produit.nom}' : "
                    f"demandé {ligne_data['quantite']}, disponible {produit.quantite_stock}."
                )
        if erreurs:
            raise serializers.ValidationError({"stock": erreurs})

        # Créer les nouvelles lignes
        remise = validated_data.get("remise", 0)
        for ligne_data in validated_data["lignes"]:
            produit = Produit.objects.get(pk=ligne_data["produit"])
            LigneVente.objects.create(
                vente=instance,
                produit=produit,
                quantite=ligne_data["quantite"],
                prix_unitaire=produit.prix_vente,
                prix_special=ligne_data.get("prix_special"),
            )
            ajuster_stock(
                produit=produit,
                quantite=-ligne_data["quantite"],
                type_mouvement="sortie",
                motif=f"Vente modifiée {instance.reference}",
                reference=instance.reference,
            )

        instance.remise = remise
        instance.notes = validated_data.get("notes", instance.notes)
        instance.save()
        instance.calculer_totaux()
        return instance

