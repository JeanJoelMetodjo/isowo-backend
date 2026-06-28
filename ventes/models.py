from django.db import models
from clients.models import Client
from authentification.models import Utilisateur


class Vente(models.Model):
    STATUT_CHOICES = [
        ("validee", "Validée"),
        ("partielle", "Partielle"),
        ("annulee", "Annulée"),
    ]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(
        Client, on_delete=models.PROTECT, related_name="ventes"
    )
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name="ventes"
    )
    remise = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_paye = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    solde_restant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="validee")
    notes = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ventes"
        verbose_name = "Vente"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.reference} — {self.client}"

    def generer_reference(self):
        from django.utils import timezone
        annee = timezone.now().year
        derniere = Vente.objects.filter(
            reference__startswith=f"VNT-{annee}-"
        ).order_by("-reference").first()
        if derniere:
            numero = int(derniere.reference.split("-")[-1]) + 1
        else:
            numero = 1
        return f"VNT-{annee}-{numero:03d}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generer_reference()
        super().save(*args, **kwargs)

    def calculer_totaux(self):
        from django.db.models import Sum
        sous_total = self.lignes.aggregate(
            total=Sum("prix_total")
        )["total"] or 0
        self.montant_total = sous_total - self.remise
        total_paiements = self.paiements.aggregate(
            total=Sum("montant")
        )["total"] or 0
        self.montant_paye = total_paiements
        self.solde_restant = self.montant_total - self.montant_paye
        if self.solde_restant <= 0:
            self.statut = "validee"
        else:
            self.statut = "partielle"
        self.save()


class LigneVente(models.Model):
    vente = models.ForeignKey(
        Vente, on_delete=models.CASCADE, related_name="lignes"
    )
    produit = models.ForeignKey(
        "produits.Produit", on_delete=models.PROTECT, related_name="lignes_vente"
    )
    quantite = models.IntegerField()
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    prix_special = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Prix spécial pour cette ligne (remplace le prix unitaire)"
    )
    prix_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "lignes_vente"

    def __str__(self):
        return f"{self.vente.reference} — {self.produit.nom} x{self.quantite}"

    @property
    def prix_effectif(self):
        return self.prix_special if self.prix_special else self.prix_unitaire

    def save(self, *args, **kwargs):
        self.prix_total = self.prix_effectif * self.quantite
        super().save(*args, **kwargs)



class VersionFacture(models.Model):
    vente = models.ForeignKey(
        Vente, on_delete=models.CASCADE, related_name="versions"
    )
    version = models.IntegerField()
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    montant_paye = models.DecimalField(max_digits=12, decimal_places=2)
    solde_restant = models.DecimalField(max_digits=12, decimal_places=2)
    statut = models.CharField(max_length=20)
    motif = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(
        "authentification.Utilisateur",
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        db_table = "versions_factures"
        ordering = ["-version"]

    def __str__(self):
        return f"{self.vente.reference} v{self.version}"