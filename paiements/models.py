from django.db import models
from clients.models import Client
from ventes.models import Vente
from authentification.models import Utilisateur


class PaiementClient(models.Model):
    vente = models.ForeignKey(
        Vente, on_delete=models.CASCADE, related_name="paiements"
    )
    client = models.ForeignKey(
        Client, on_delete=models.PROTECT, related_name="paiements"
    )
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name="paiements_clients"
    )
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "paiements_clients"
        verbose_name = "Paiement client"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.vente.reference} — {self.montant} FCFA"