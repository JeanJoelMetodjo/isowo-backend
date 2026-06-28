from django.db import models
from produits.models import Produit


class Stock(models.Model):
    produit = models.OneToOneField(
        Produit, on_delete=models.CASCADE, related_name="stock"
    )
    quantite = models.IntegerField(default=0)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stock"

    def __str__(self):
        return f"{self.produit.nom} — {self.quantite}"


class MouvementStock(models.Model):
    TYPE_CHOICES = [
        ("entree", "Entrée"),
        ("sortie", "Sortie"),
        ("ajustement", "Ajustement"),
        ("retour_vente", "Retour vente"),
        ("retour_pret", "Retour prêt"),
        ("pret", "Prêt"),
    ]

    produit = models.ForeignKey(
        Produit, on_delete=models.CASCADE, related_name="mouvements"
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantite = models.IntegerField()
    quantite_avant = models.IntegerField()
    quantite_apres = models.IntegerField()
    motif = models.CharField(max_length=300, blank=True)
    reference = models.CharField(max_length=50, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mouvements_stock"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.type} — {self.produit.nom} — {self.quantite}"