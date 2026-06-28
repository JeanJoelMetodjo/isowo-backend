from rest_framework import generics, status
from rest_framework.response import Response
from historique.utils import enregistrer_action
from .models import Categorie
from .serializers import CategorieSerializer
from authentification.permissions import EstAdmin, EstAdminOuLecture


class CategorieListCreateView(generics.ListCreateAPIView):
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    permission_classes = [EstAdminOuLecture]

    def get_queryset(self):
        queryset = Categorie.objects.all()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(nom__icontains=search)
        return queryset

    def perform_create(self, serializer):
        categorie = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="creation",
            module="categories",
            reference=str(categorie.pk),
            description=f"Catégorie {categorie.nom} créée.",
            request=self.request,
        )


class CategorieDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    permission_classes = [EstAdminOuLecture]

    def perform_update(self, serializer):
        categorie = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="modification",
            module="categories",
            reference=str(categorie.pk),
            description=f"Catégorie {categorie.nom} modifiée.",
            request=self.request,
        )

    def destroy(self, request, *args, **kwargs):
        categorie = self.get_object()
        if categorie.produits.exists():
            return Response(
                {"detail": f"Impossible de supprimer : {categorie.produits.count()} produit(s) utilisent cette catégorie."},
                status=status.HTTP_400_BAD_REQUEST
            )
        reference = str(categorie.pk)
        response = super().destroy(request, *args, **kwargs)
        if response.status_code in (200, 204):
            enregistrer_action(
                utilisateur=request.user,
                type_action="suppression",
                module="categories",
                reference=reference,
                description=f"Catégorie {categorie.nom} supprimée.",
                request=request,
            )
        return response