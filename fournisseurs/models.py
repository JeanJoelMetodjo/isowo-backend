from django.db import models


class Fournisseur(models.Model):
    nom_entreprise = models.CharField(max_length=200)
    nom_contact = models.CharField(max_length=100, blank=True)
    prenom_contact = models.CharField(max_length=100, blank=True)
    adresse = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    delai_paiement = models.IntegerField(default=0, help_text="Délai habituel en jours")
    notes = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fournisseurs"
        verbose_name = "Fournisseur"
        ordering = ["nom_entreprise"]

    def __str__(self):
        return self.nom_entreprise

    @property
    def solde_du(self):
        from django.db.models import Sum
        result = self.achats.filter(
            statut__in=["valide", "partiel"]
        ).aggregate(total=Sum("solde_restant"))
        return result["total"] or 0


class FournisseurTelephone(models.Model):
    TYPE_CHOICES = [
        ("principal", "Principal"),
        ("secondaire", "Secondaire"),
        ("professionnel", "Professionnel"),
    ]

    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.CASCADE, related_name="telephones")
    numero = models.CharField(max_length=20)
    compagnie = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="principal")

    class Meta:
        db_table = "fournisseur_telephones"

    def __str__(self):
        return f"{self.numero} ({self.type})"