from rest_framework import serializers
from .models import Fournisseur, FournisseurTelephone


class FournisseurTelephoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = FournisseurTelephone
        fields = ["id", "numero", "compagnie", "type"]


class FournisseurSerializer(serializers.ModelSerializer):
    telephones = FournisseurTelephoneSerializer(many=True, read_only=True)
    solde_du = serializers.ReadOnlyField()

    class Meta:
        model = Fournisseur
        fields = [
            "id", "nom_entreprise", "nom_contact", "prenom_contact",
            "adresse", "email", "delai_paiement", "notes", "solde_du",
            "telephones", "date_creation", "date_modification"
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class FournisseurCreateUpdateSerializer(serializers.ModelSerializer):
    telephones = FournisseurTelephoneSerializer(many=True, required=False)

    class Meta:
        model = Fournisseur
        fields = [
            "id", "nom_entreprise", "nom_contact", "prenom_contact",
            "adresse", "email", "delai_paiement", "notes", "telephones"
        ]

    def create(self, validated_data):
        telephones_data = validated_data.pop("telephones", [])
        fournisseur = Fournisseur.objects.create(**validated_data)
        for tel in telephones_data:
            FournisseurTelephone.objects.create(fournisseur=fournisseur, **tel)
        return fournisseur

    def update(self, instance, validated_data):
        telephones_data = validated_data.pop("telephones", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if telephones_data is not None:
            instance.telephones.all().delete()
            for tel in telephones_data:
                FournisseurTelephone.objects.create(fournisseur=instance, **tel)
        return instance