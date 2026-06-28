from django.db import models


class Client(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True)
    adresse = models.TextField(blank=True)
    observations = models.TextField(blank=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients"
        verbose_name = "Client"
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.nom} {self.prenom}".strip()

    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}".strip()

    @property
    def solde_du(self):
        from django.db.models import Sum
        from ventes.models import Vente
        result = self.ventes.filter(
            statut__in=["validee", "partielle"]
        ).aggregate(total=Sum("solde_restant"))
        return result["total"] or 0


class ClientTelephone(models.Model):
    TYPE_CHOICES = [
        ("principal", "Principal"),
        ("secondaire", "Secondaire"),
        ("professionnel", "Professionnel"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="telephones")
    numero = models.CharField(max_length=20)
    compagnie = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="principal")

    class Meta:
        db_table = "client_telephones"

    def __str__(self):
        return f"{self.numero} ({self.type})"


class ClientContactUrgence(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="contacts_urgence")
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20)
    relation = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "client_contacts_urgence"

    def __str__(self):
        return f"{self.nom} {self.prenom} — {self.relation}"