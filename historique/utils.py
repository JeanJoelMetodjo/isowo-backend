from .models import HistoriqueAction


def enregistrer_action(
    utilisateur,
    type_action,
    module,
    description,
    reference="",
    donnees_avant=None,
    donnees_apres=None,
    request=None,
):
    adresse_ip = None
    if request:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            adresse_ip = x_forwarded_for.split(",")[0].strip()
        else:
            adresse_ip = request.META.get("REMOTE_ADDR")

    HistoriqueAction.objects.create(
        utilisateur=utilisateur,
        type_action=type_action,
        module=module,
        reference=reference,
        description=description,
        donnees_avant=donnees_avant,
        donnees_apres=donnees_apres,
        adresse_ip=adresse_ip,
    )