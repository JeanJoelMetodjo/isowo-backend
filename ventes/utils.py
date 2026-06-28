def creer_version_facture(vente, motif="", utilisateur=None):
    from .models import VersionFacture
    derniere = VersionFacture.objects.filter(vente=vente).order_by("-version").first()
    numero = (derniere.version + 1) if derniere else 1
    VersionFacture.objects.create(
        vente=vente,
        version=numero,
        montant_total=vente.montant_total,
        montant_paye=vente.montant_paye,
        solde_restant=vente.solde_restant,
        statut=vente.statut,
        motif=motif,
        cree_par=utilisateur,
    )