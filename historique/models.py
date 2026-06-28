from django.db import models
from authentification.models import Utilisateur


class HistoriqueAction(models.Model):
    TYPE_CHOICES = [
        ("creation", "Création"),
        ("modification", "Modification"),
        ("suppression", "Suppression"),
        ("annulation", "Annulation"),
        ("paiement", "Paiement"),
        ("connexion", "Connexion"),
    ]

    MODULE_CHOICES = [
        ("ventes", "Ventes"),
        ("achats", "Achats"),
        ("clients", "Clients"),
        ("fournisseurs", "Fournisseurs"),
        ("produits", "Produits"),
        ("stock", "Stock"),
        ("paiements", "Paiements"),
        ("prets", "Prêts"),
        ("utilisateurs", "Utilisateurs"),
        ("auth", "Authentification"),
    ]

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name="historique"
    )
    type_action = models.CharField(max_length=20, choices=TYPE_CHOICES)
    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    reference = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    donnees_avant = models.JSONField(null=True, blank=True)
    donnees_apres = models.JSONField(null=True, blank=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historique_actions"
        verbose_name = "Action"
        verbose_name_plural = "Historique des actions"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.type_action} — {self.module} — {self.date}"