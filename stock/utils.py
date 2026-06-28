from .models import Stock, MouvementStock


def ajuster_stock(produit, quantite, type_mouvement, motif="", reference=""):
    """
    Ajuste le stock d'un produit et enregistre le mouvement.
    quantite positive = entrée, negative = sortie.
    Retourne le stock mis à jour.
    """
    stock, _ = Stock.objects.get_or_create(produit=produit)
    quantite_avant = stock.quantite
    stock.quantite += quantite
    stock.save()

    MouvementStock.objects.create(
        produit=produit,
        type=type_mouvement,
        quantite=abs(quantite),
        quantite_avant=quantite_avant,
        quantite_apres=stock.quantite,
        motif=motif,
        reference=reference,
    )
    return stock