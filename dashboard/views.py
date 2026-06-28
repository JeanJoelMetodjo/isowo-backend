from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "chiffre_affaires": self._chiffre_affaires(None, None),
            "clients": self._stats_clients(),
            "produits": self._stats_produits(),
            "stock": self._stats_stock(),
            "dettes": self._stats_dettes(),
            "prets": self._stats_prets(),
        })

    # def _chiffre_affaires(self, aujourd_hui, debut_mois):
    #     from ventes.models import Vente

    #     ca_jour = Vente.objects.filter(
    #         date__date=aujourd_hui,
    #         statut__in=["validee", "partielle"]
    #     ).aggregate(total=Sum("montant_total"))["total"] or 0

    #     ca_mois = Vente.objects.filter(
    #         date__date__gte=debut_mois,
    #         statut__in=["validee", "partielle"]
    #     ).aggregate(total=Sum("montant_total"))["total"] or 0

    #     paye_jour = Vente.objects.filter(
    #         date__date=aujourd_hui,
    #         statut__in=["validee", "partielle"]
    #     ).aggregate(total=Sum("montant_paye"))["total"] or 0

    #     paye_mois = Vente.objects.filter(
    #         date__date__gte=debut_mois,
    #         statut__in=["validee", "partielle"]
    #     ).aggregate(total=Sum("montant_paye"))["total"] or 0

    #     nb_ventes_jour = Vente.objects.filter(
    #         date__date=aujourd_hui,
    #         statut__in=["validee", "partielle"]
    #     ).count()

    #     nb_ventes_mois = Vente.objects.filter(
    #         date__date__gte=debut_mois,
    #         statut__in=["validee", "partielle"]
    #     ).count()

    #     return {
    #         "ca_jour": ca_jour,
    #         "ca_mois": ca_mois,
    #         "paye_jour": paye_jour,
    #         "paye_mois": paye_mois,
    #         "nb_ventes_jour": nb_ventes_jour,
    #         "nb_ventes_mois": nb_ventes_mois,
    #     }
      
    def _chiffre_affaires(self, aujourd_hui, debut_mois):
        from ventes.models import Vente

        # Utiliser now() localisé plutôt que date() brut
        maintenant = timezone.localtime(timezone.now())
        debut_jour = maintenant.replace(hour=0, minute=0, second=0, microsecond=0)
        fin_jour = debut_jour + timedelta(days=1)

        debut_mois_dt = maintenant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        ca_jour = Vente.objects.filter(
            date__gte=debut_jour,
            date__lt=fin_jour,
            statut__in=["validee", "partielle"]
        ).aggregate(total=Sum("montant_total"))["total"] or 0

        ca_mois = Vente.objects.filter(
            date__gte=debut_mois_dt,
            statut__in=["validee", "partielle"]
        ).aggregate(total=Sum("montant_total"))["total"] or 0

        paye_jour = Vente.objects.filter(
            date__gte=debut_jour,
            date__lt=fin_jour,
            statut__in=["validee", "partielle"]
        ).aggregate(total=Sum("montant_paye"))["total"] or 0

        paye_mois = Vente.objects.filter(
            date__gte=debut_mois_dt,
            statut__in=["validee", "partielle"]
        ).aggregate(total=Sum("montant_paye"))["total"] or 0

        nb_ventes_jour = Vente.objects.filter(
            date__gte=debut_jour,
            date__lt=fin_jour,
            statut__in=["validee", "partielle"]
        ).count()

        nb_ventes_mois = Vente.objects.filter(
            date__gte=debut_mois_dt,
            statut__in=["validee", "partielle"]
        ).count()

        return {
            "ca_jour": ca_jour,
            "ca_mois": ca_mois,
            "paye_jour": paye_jour,
            "paye_mois": paye_mois,
            "nb_ventes_jour": nb_ventes_jour,
            "nb_ventes_mois": nb_ventes_mois,
        }
    def _stats_clients(self):
        from clients.models import Client
        from ventes.models import Vente

        total_clients = Client.objects.count()

        top_debiteurs = (
            Vente.objects
            .filter(statut="partielle")
            .values("client__id", "client__nom", "client__prenom")
            .annotate(total_du=Sum("solde_restant"))
            .order_by("-total_du")[:5]
        )

        return {
            "total": total_clients,
            "top_debiteurs": list(top_debiteurs),
        }

    def _stats_produits(self):
        from produits.models import Produit

        total = Produit.objects.count()
        actifs = Produit.objects.filter(est_actif=True).count()
        inactifs = Produit.objects.filter(est_actif=False).count()

        return {
            "total": total,
            "actifs": actifs,
            "inactifs": inactifs,
        }

    def _stats_stock(self):
        from produits.models import Produit
        from django.db.models import F

        en_rupture = Produit.objects.filter(
            est_actif=True,
            stock__quantite=0
        ).values("id", "code", "nom", "seuil_alerte")

        sous_seuil = Produit.objects.filter(
            est_actif=True,
            stock__quantite__gt=0,
            stock__quantite__lte=F("seuil_alerte")
        ).values("id", "code", "nom", "seuil_alerte", "stock__quantite")

        return {
            "en_rupture": list(en_rupture),
            "nb_rupture": len(en_rupture),
            "sous_seuil": list(sous_seuil),
            "nb_sous_seuil": len(sous_seuil),
        }

    def _stats_dettes(self):
        from ventes.models import Vente
        from achats.models import AchatFournisseur

        # Dettes clients
        total_du_clients = Vente.objects.filter(
            statut="partielle"
        ).aggregate(total=Sum("solde_restant"))["total"] or 0

        nb_ventes_en_attente = Vente.objects.filter(statut="partielle").count()

        # Dettes fournisseurs
        total_du_fournisseurs = AchatFournisseur.objects.filter(
            statut="partiel"
        ).aggregate(total=Sum("solde_restant"))["total"] or 0

        nb_achats_en_attente = AchatFournisseur.objects.filter(statut="partiel").count()

        # Top fournisseurs créditeurs
        top_fournisseurs = (
            AchatFournisseur.objects
            .filter(statut="partiel")
            .values("fournisseur__id", "fournisseur__nom_entreprise")
            .annotate(total_du=Sum("solde_restant"))
            .order_by("-total_du")[:5]
        )

        return {
            "clients": {
                "total_du": total_du_clients,
                "nb_en_attente": nb_ventes_en_attente,
            },
            "fournisseurs": {
                "total_du": total_du_fournisseurs,
                "nb_en_attente": nb_achats_en_attente,
                "top": list(top_fournisseurs),
            },
        }

    def _stats_prets(self):
        from prets.models import PretMarchandise, PretArgent

        # Prêts marchandises
        prets_marchandises = PretMarchandise.objects.filter(
            statut__in=["en_cours", "partiel"]
        ).values(
            "id", "reference", "beneficiaire",
            "produit__nom", "quantite", "quantite_rendue",
            "date_retour_prevue"
        )

        # Prêts argent
        prets_argent = PretArgent.objects.filter(
            statut__in=["en_cours", "partiel"]
        ).values(
            "id", "reference", "beneficiaire",
            "montant", "solde_restant", "date_retour_prevue"
        )

        total_argent_en_cours = PretArgent.objects.filter(
            statut__in=["en_cours", "partiel"]
        ).aggregate(total=Sum("solde_restant"))["total"] or 0

        return {
            "marchandises": {
                "en_cours": list(prets_marchandises),
                "nb": len(prets_marchandises),
            },
            "argent": {
                "en_cours": list(prets_argent),
                "nb": len(prets_argent),
                "total_restant": total_argent_en_cours,
            },
        }


class DashboardVentesGraphView(APIView):
    """Ventes des 30 derniers jours — pour graphique."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ventes.models import Vente

        aujourd_hui = timezone.now().date()
        il_y_a_30_jours = aujourd_hui - timedelta(days=29)

        ventes_par_jour = (
            Vente.objects
            .filter(
                date__date__gte=il_y_a_30_jours,
                statut__in=["validee", "partielle"]
            )
            .values("date__date")
            .annotate(
                total=Sum("montant_total"),
                paye=Sum("montant_paye"),
                nb=Count("id")
            )
            .order_by("date__date")
        )

        return Response({
            "periode": {
                "debut": il_y_a_30_jours,
                "fin": aujourd_hui,
            },
            "ventes_par_jour": list(ventes_par_jour),
        })


class DashboardTopProduitsView(APIView):
    """Top 10 produits les plus vendus."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ventes.models import LigneVente

        aujourd_hui = timezone.now().date()
        debut_mois = aujourd_hui.replace(day=1)

        top_produits = (
            LigneVente.objects
            .filter(
                vente__statut__in=["validee", "partielle"],
                vente__date__date__gte=debut_mois,
            )
            .values("produit__id", "produit__nom", "produit__code")
            .annotate(
                quantite_vendue=Sum("quantite"),
                chiffre_affaires=Sum("prix_total")
            )
            .order_by("-quantite_vendue")[:10]
        )

        return Response({"top_produits": list(top_produits)})