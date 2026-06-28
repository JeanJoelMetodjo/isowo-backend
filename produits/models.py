from django.db import models
from categories.models import Categorie
from fournisseurs.models import Fournisseur


class Produit(models.Model):
    code = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=200)
    marque = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    couleur = models.CharField(max_length=50, blank=True)
    poids_volume = models.CharField(max_length=50, blank=True)
    categorie = models.ForeignKey(
        Categorie, on_delete=models.PROTECT,
        related_name="produits", null=True, blank=True
    )
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.SET_NULL,
        related_name="produits", null=True, blank=True
    )
    prix_achat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    prix_vente = models.DecimalField(max_digits=12, decimal_places=2)
    seuil_alerte = models.IntegerField(default=5)
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "produits"
        verbose_name = "Produit"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.code} — {self.nom}"

    @property
    def quantite_stock(self):
        try:
            return self.stock.quantite
        except Exception:
            return 0

    @property
    def en_alerte(self):
        return self.quantite_stock <= self.seuil_alerte