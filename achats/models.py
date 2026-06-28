from django.db import models
from fournisseurs.models import Fournisseur
from authentification.models import Utilisateur


class AchatFournisseur(models.Model):
    STATUT_CHOICES = [
        ("valide", "Validé"),
        ("partiel", "Partiel"),
        ("annule", "Annulé"),
    ]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.PROTECT, related_name="achats"
    )
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name="achats"
    )
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_paye = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    solde_restant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="valide")
    notes = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "achats_fournisseurs"
        verbose_name = "Achat fournisseur"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.reference} — {self.fournisseur}"

    def generer_reference(self):
        from django.utils import timezone
        annee = timezone.now().year
        derniere = AchatFournisseur.objects.filter(
            reference__startswith=f"ACH-{annee}-"
        ).order_by("-reference").first()
        if derniere:
            numero = int(derniere.reference.split("-")[-1]) + 1
        else:
            numero = 1
        return f"ACH-{annee}-{numero:03d}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generer_reference()
        super().save(*args, **kwargs)

    def calculer_totaux(self):
        from django.db.models import Sum
        total_paiements = self.paiements.aggregate(
            total=Sum("montant")
        )["total"] or 0
        self.montant_paye = total_paiements
        self.solde_restant = self.montant_total - self.montant_paye
        if self.solde_restant <= 0:
            self.solde_restant = 0
            self.statut = "valide"
        else:
            self.statut = "partiel"
        self.save()


class LigneAchat(models.Model):
    achat = models.ForeignKey(
        AchatFournisseur, on_delete=models.CASCADE, related_name="lignes"
    )
    produit = models.ForeignKey(
        "produits.Produit", on_delete=models.PROTECT, related_name="lignes_achat"
    )
    quantite = models.IntegerField()
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    prix_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "lignes_achat"

    def __str__(self):
        return f"{self.achat.reference} — {self.produit.nom} x{self.quantite}"

    def save(self, *args, **kwargs):
        self.prix_total = self.prix_unitaire * self.quantite
        super().save(*args, **kwargs)


class PaiementFournisseur(models.Model):
    achat = models.ForeignKey(
        AchatFournisseur, on_delete=models.CASCADE, related_name="paiements"
    )
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.PROTECT, related_name="paiements"
    )
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name="paiements_fournisseurs"
    )
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "paiements_fournisseurs"
        verbose_name = "Paiement fournisseur"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.achat.reference} — {self.montant} FCFA"