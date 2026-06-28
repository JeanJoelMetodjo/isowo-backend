from django.db import models
from authentification.models import Utilisateur


class PretMarchandise(models.Model):
    STATUT_CHOICES = [
        ("en_cours", "En cours"),
        ("rembourse", "Remboursé"),
        ("partiel", "Partiel"),
    ]

    MODE_REMBOURSEMENT_CHOICES = [
        ("produit", "Restitution produit"),
        ("argent", "Remboursement argent"),
    ]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    beneficiaire = models.CharField(max_length=200)
    produit = models.ForeignKey(
        "produits.Produit", on_delete=models.PROTECT, related_name="prets"
    )
    quantite = models.IntegerField()
    quantite_rendue = models.IntegerField(default=0)
    mode_remboursement = models.CharField(
        max_length=20, choices=MODE_REMBOURSEMENT_CHOICES, default="produit"
    )
    montant_equivalent = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Valeur en argent si remboursement en argent"
    )
    montant_rembourse = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_pret = models.DateTimeField(auto_now_add=True)
    date_retour_prevue = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_cours")
    notes = models.TextField(blank=True)
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name="prets_marchandises"
    )

    class Meta:
        db_table = "prets_marchandises"
        verbose_name = "Prêt de marchandise"
        ordering = ["-date_pret"]

    def __str__(self):
        return f"{self.reference} — {self.beneficiaire}"

    def generer_reference(self):
        from django.utils import timezone
        annee = timezone.now().year
        derniere = PretMarchandise.objects.filter(
            reference__startswith=f"PLM-{annee}-"
        ).order_by("-reference").first()
        if derniere:
            numero = int(derniere.reference.split("-")[-1]) + 1
        else:
            numero = 1
        return f"PLM-{annee}-{numero:03d}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generer_reference()
        super().save(*args, **kwargs)


class RemboursementMarchandise(models.Model):
    pret = models.ForeignKey(
        PretMarchandise, on_delete=models.CASCADE, related_name="remboursements"
    )
    quantite_rendue = models.IntegerField(default=0)
    montant_paye = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name="remboursements_marchandises"
    )

    class Meta:
        db_table = "remboursements_marchandises"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.pret.reference} — remboursement {self.date}"


class PretArgent(models.Model):
    STATUT_CHOICES = [
        ("en_cours", "En cours"),
        ("rembourse", "Remboursé"),
        ("partiel", "Partiel"),
    ]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    beneficiaire = models.CharField(max_length=200)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    montant_rembourse = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    solde_restant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_pret = models.DateTimeField(auto_now_add=True)
    date_retour_prevue = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_cours")
    notes = models.TextField(blank=True)
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name="prets_argent"
    )

    class Meta:
        db_table = "prets_argent"
        verbose_name = "Prêt d'argent"
        ordering = ["-date_pret"]

    def __str__(self):
        return f"{self.reference} — {self.beneficiaire}"

    def generer_reference(self):
        from django.utils import timezone
        annee = timezone.now().year
        derniere = PretArgent.objects.filter(
            reference__startswith=f"PLA-{annee}-"
        ).order_by("-reference").first()
        if derniere:
            numero = int(derniere.reference.split("-")[-1]) + 1
        else:
            numero = 1
        return f"PLA-{annee}-{numero:03d}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generer_reference()
        if not self.pk:
            self.solde_restant = self.montant
        super().save(*args, **kwargs)

    def calculer_solde(self):
        from django.db.models import Sum
        total = self.remboursements.aggregate(
            total=Sum("montant")
        )["total"] or 0
        self.montant_rembourse = total
        self.solde_restant = self.montant - total
        if self.solde_restant <= 0:
            self.solde_restant = 0
            self.statut = "rembourse"
        else:
            self.statut = "partiel"
        self.save()


class RemboursementArgent(models.Model):
    pret = models.ForeignKey(
        PretArgent, on_delete=models.CASCADE, related_name="remboursements"
    )
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name="remboursements_argent"
    )

    class Meta:
        db_table = "remboursements_argent"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.pret.reference} — {self.montant} FCFA"