# from django.core.mail import send_mail
# from django.conf import settings


# def envoyer_code(utilisateur, objet="Vérification de votre compte Isowo"):
#     code = utilisateur.generer_code()
#     message = f"""Bonjour {utilisateur.nom},

# Voici votre code : {code}

# Ce code est valable 15 minutes.

# L'équipe Isowo
# """
#     send_mail(objet, message, settings.DEFAULT_FROM_EMAIL, [utilisateur.email], fail_silently=False)


import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings


def envoyer_code(utilisateur, objet="Vérification de votre compte Isowo"):
    code = utilisateur.generer_code()
    message = f"""Bonjour {utilisateur.nom},

Voici votre code : {code}

Ce code est valable 15 minutes.

L'équipe Isowo
"""
    if not settings.BREVO_API_KEY:
        raise RuntimeError("BREVO_API_KEY n'est pas configurée")

    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": utilisateur.email, "name": utilisateur.nom}],
            sender={"email": settings.DEFAULT_FROM_EMAIL, "name": getattr(settings, "BREVO_SENDER_NAME", "Isowo")},
            subject=objet,
            text_content=message,
        )
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print(f"Erreur envoi email Brevo: {e}")
        raise e