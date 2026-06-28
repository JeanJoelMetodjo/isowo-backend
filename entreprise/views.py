from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Entreprise
from .serializers import EntrepriseSerializer
from authentification.permissions import EstAdmin


class EntrepriseView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entreprise = Entreprise.objects.first()
        if not entreprise:
            return Response(None, status=status.HTTP_200_OK)
        serializer = EntrepriseSerializer(entreprise, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        """Création initiale de l'entreprise."""
        entreprise_existante = Entreprise.objects.first()
        if entreprise_existante:
            # Déjà une entreprise — on met à jour au lieu de créer
            serializer = EntrepriseSerializer(
                entreprise_existante,
                data=request.data,
                partial=True,
                context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = EntrepriseSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            entreprise = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """Mise à jour de l'entreprise."""
        entreprise = Entreprise.objects.first()
        if not entreprise:
            # Pas encore d'entreprise — on crée
            serializer = EntrepriseSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = EntrepriseSerializer(
            entreprise,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)