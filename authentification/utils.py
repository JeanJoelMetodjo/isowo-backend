from django.core.mail import send_mail
from django.conf import settings


def envoyer_code(utilisateur, objet="Vérification de votre compte Isowo"):
    code = utilisateur.generer_code()
    message = f"""Bonjour {utilisateur.nom},

Voici votre code : {code}

Ce code est valable 15 minutes.

L'équipe Isowo
"""
    send_mail(objet, message, settings.DEFAULT_FROM_EMAIL, [utilisateur.email], fail_silently=False)