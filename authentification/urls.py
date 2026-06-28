from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("inscription/", views.InscriptionView.as_view(), name="inscription"),
    path("verification/", views.VerificationEmailView.as_view(), name="verification"),
    path("renvoyer-code/", views.RenvoyerCodeView.as_view(), name="renvoyer_code"),
    path("mot-de-passe-oublie/", views.DemandeReinitialisationView.as_view(), name="mdp_oublie"),
    path("reinitialiser-mot-de-passe/", views.ReinitialiserMotDePasseView.as_view(), name="reinitialiser_mdp"),

    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("moi/", views.MoiView.as_view(), name="moi"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("utilisateurs/", views.UtilisateurListCreateView.as_view(), name="utilisateurs"),
    path("utilisateurs/<int:pk>/", views.UtilisateurDetailView.as_view(), name="utilisateur_detail"),
    path("mot-de-passe/", views.ModifierMotDePasseView.as_view(), name="modifier_mdp"),
    path("profil/", views.ModifierProfilView.as_view(), name="modifier_profil"),
]