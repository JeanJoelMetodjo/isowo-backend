from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from historique.utils import enregistrer_action
from .models import Utilisateur
from .serializers import UtilisateurSerializer, CreerUtilisateurSerializer, ModifierMotDePasseSerializer
from .permissions import EstAdmin


from .serializers import (
    InscriptionSerializer, VerificationEmailSerializer, RenvoyerCodeSerializer,
    DemandeReinitialisationSerializer, ReinitialiserMotDePasseSerializer,
)
from .utils import envoyer_code


# class InscriptionView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = InscriptionSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             envoyer_code(user, "Vérification de votre compte Isowo")
#             return Response({
#                 "detail": "Compte créé. Un code de vérification a été envoyé par email.",
#                 "email": user.email,
#             }, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InscriptionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InscriptionSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            try:
                envoyer_code(user, "Vérification de votre compte Isowo")
            except Exception as e:
                return Response({
                    "detail": "Compte créé mais l'envoi de l'email a échoué. Contactez le support.",
                    "email": user.email,
                }, status=status.HTTP_201_CREATED)
            return Response({
                "detail": "Compte créé. Un code de vérification a été envoyé par email.",
                "email": user.email,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerificationEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerificationEmailSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["_user"]
            user.email_verifie = True
            user.est_actif = True
            user.code_verification = ""
            user.code_expiration = None
            user.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                "detail": "Compte vérifié avec succès.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "utilisateur": UtilisateurSerializer(user).data,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RenvoyerCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RenvoyerCodeSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["_user"]
            motif = serializer.validated_data["motif"]
            objet = "Vérification de votre compte Isowo" if motif == "verification" else "Réinitialisation de votre mot de passe Isowo"
            envoyer_code(user, objet)
            return Response({"detail": "Code envoyé par email."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DemandeReinitialisationView(APIView):
    """Mot de passe oublié — étape 1 : demande du code."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DemandeReinitialisationSerializer(data=request.data)
        if serializer.is_valid():
            user = Utilisateur.objects.get(email=serializer.validated_data["email"])
            envoyer_code(user, "Réinitialisation de votre mot de passe Isowo")
            return Response({"detail": "Code de réinitialisation envoyé par email."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReinitialiserMotDePasseView(APIView):
    """Mot de passe oublié — étape 2 : vérification du code + nouveau mot de passe."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ReinitialiserMotDePasseSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["_user"]
            user.set_password(serializer.validated_data["nouveau_password"])
            user.code_verification = ""
            user.code_expiration = None
            user.save()
            return Response({"detail": "Mot de passe réinitialisé avec succès."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)

        if not user:
            return Response(
                {"detail": "Identifiants incorrects."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.email_verifie:
            return Response(
                {"detail": "Compte non vérifié. Vérifiez votre email.", "email": user.email, "non_verifie": True},
                status=status.HTTP_403_FORBIDDEN
            )

        if not user.est_actif:
            return Response(
                {"detail": "Ce compte est désactivé."},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "utilisateur": UtilisateurSerializer(user).data,
        })

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Déconnexion réussie."})
        except Exception:
            return Response({"detail": "Token invalide."}, status=status.HTTP_400_BAD_REQUEST)


class MoiView(APIView):
    """Retourne les infos de l'utilisateur connecté."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UtilisateurSerializer(request.user).data)


class UtilisateurListCreateView(generics.ListCreateAPIView):
    """Liste et création — admin seulement."""
    queryset = Utilisateur.objects.all().order_by("username")
    permission_classes = [EstAdmin]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreerUtilisateurSerializer
        return UtilisateurSerializer

    def perform_create(self, serializer):
        utilisateur = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="creation",
            module="authentification",
            reference=str(utilisateur.username),
            description=f"Utilisateur {utilisateur.username} créé.",
            request=self.request,
        )


class UtilisateurDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification, suppression — admin seulement."""
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [EstAdmin]

    def perform_update(self, serializer):
        utilisateur = serializer.save()
        enregistrer_action(
            utilisateur=self.request.user,
            type_action="modification",
            module="authentification",
            reference=str(utilisateur.username),
            description=f"Utilisateur {utilisateur.username} modifié.",
            request=self.request,
        )

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": "Vous ne pouvez pas supprimer votre propre compte."},
                status=status.HTTP_400_BAD_REQUEST
            )
        reference = str(user.username)
        response = super().destroy(request, *args, **kwargs)
        if response.status_code in (200, 204):
            enregistrer_action(
                utilisateur=request.user,
                type_action="suppression",
                module="authentification",
                reference=reference,
                description=f"Utilisateur {reference} supprimé.",
                request=request,
            )
        return response


class ModifierMotDePasseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ModifierMotDePasseSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Mot de passe modifié avec succès."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ModifierProfilView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ModifierProfilSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UtilisateurSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)