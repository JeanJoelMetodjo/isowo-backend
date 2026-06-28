import random
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import timedelta
from django.utils import timezone



class UtilisateurManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Le nom d'utilisateur est obligatoire")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("admin", "Administrateur"),
        ("caissier", "Caissier"),
    ]

    username = models.CharField(max_length=150, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="caissier")
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    email_verifie = models.BooleanField(default=True)  # True pour les comptes existants
    code_verification = models.CharField(max_length=6, blank=True)
    code_expiration = models.DateTimeField(null=True, blank=True)

    # Requis par Django
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UtilisateurManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["nom"]

    class Meta:
        db_table = "utilisateurs"
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def est_admin(self):
        return self.role == "admin"

    def generer_code(self):
        self.code_verification = f"{random.randint(0, 999999):06d}"
        self.code_expiration = timezone.now() + timedelta(minutes=15)
        self.save(update_fields=["code_verification", "code_expiration"])
        return self.code_verification

    def code_valide(self, code):
        if self.code_verification != code:
            return False
        if not self.code_expiration or timezone.now() > self.code_expiration:
            return False
        return True