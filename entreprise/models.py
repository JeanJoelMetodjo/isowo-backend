from django.db import models


class Entreprise(models.Model):
    nom = models.CharField(max_length=200)
    slogan = models.CharField(max_length=300, blank=True)
    logo = models.ImageField(upload_to="entreprise/", null=True, blank=True)
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=100, default="Bénin")
    email = models.EmailField(blank=True)
    telephone_principal = models.CharField(max_length=20, blank=True)
    telephone_secondaire = models.CharField(max_length=20, blank=True)
    site_web = models.URLField(blank=True)
    numero_ifu = models.CharField(max_length=100, blank=True, verbose_name="Numéro IFU")
    registre_commerce = models.CharField(max_length=100, blank=True, verbose_name="Registre de commerce")
    monnaie = models.CharField(max_length=10, default="FCFA")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entreprise"
        verbose_name = "Entreprise"

    def __str__(self):
        return self.nom