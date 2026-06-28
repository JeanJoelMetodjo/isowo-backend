from rest_framework import serializers
from .models import Client, ClientTelephone, ClientContactUrgence


class ClientTelephoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientTelephone
        fields = ["id", "numero", "compagnie", "type"]


class ClientContactUrgenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientContactUrgence
        fields = ["id", "nom", "prenom", "telephone", "relation"]


class ClientSerializer(serializers.ModelSerializer):
    telephones = ClientTelephoneSerializer(many=True, read_only=True)
    contacts_urgence = ClientContactUrgenceSerializer(many=True, read_only=True)
    solde_du = serializers.ReadOnlyField()
    nom_complet = serializers.ReadOnlyField()

    class Meta:
        model = Client
        fields = [
            "id", "nom", "prenom", "nom_complet", "adresse",
            "observations", "solde_du", "telephones",
            "contacts_urgence", "date_inscription", "date_modification"
        ]
        read_only_fields = ["id", "date_inscription", "date_modification"]


class ClientCreateUpdateSerializer(serializers.ModelSerializer):
    telephones = ClientTelephoneSerializer(many=True, required=False)
    contacts_urgence = ClientContactUrgenceSerializer(many=True, required=False)

    class Meta:
        model = Client
        fields = [
            "id", "nom", "prenom", "adresse", "observations",
            "telephones", "contacts_urgence"
        ]

    def create(self, validated_data):
        telephones_data = validated_data.pop("telephones", [])
        contacts_data = validated_data.pop("contacts_urgence", [])

        client = Client.objects.create(**validated_data)

        for tel in telephones_data:
            ClientTelephone.objects.create(client=client, **tel)
        for contact in contacts_data:
            ClientContactUrgence.objects.create(client=client, **contact)

        return client

    def update(self, instance, validated_data):
        telephones_data = validated_data.pop("telephones", None)
        contacts_data = validated_data.pop("contacts_urgence", None)

        # Mettre à jour les champs simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Remplacer les téléphones si fournis
        if telephones_data is not None:
            instance.telephones.all().delete()
            for tel in telephones_data:
                ClientTelephone.objects.create(client=instance, **tel)

        # Remplacer les contacts si fournis
        if contacts_data is not None:
            instance.contacts_urgence.all().delete()
            for contact in contacts_data:
                ClientContactUrgence.objects.create(client=instance, **contact)

        return instance