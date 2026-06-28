from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Utilisateur


def normalize_email(value):
    return value.strip().lower()


class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ["id", "username", "email", "nom", "prenom", "role", "est_actif", "email_verifie", "date_creation"]
        read_only_fields = ["id", "date_creation"]


class CreerUtilisateurSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = Utilisateur
        fields = ["username", "email", "nom", "prenom", "role", "password", "password2"]

    def validate_email(self, value):
        value = normalize_email(value)
        if Utilisateur.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = Utilisateur(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ModifierMotDePasseSerializer(serializers.Serializer):
    ancien_password = serializers.CharField(write_only=True)
    nouveau_password = serializers.CharField(write_only=True, validators=[validate_password])
    nouveau_password2 = serializers.CharField(write_only=True)

    def validate_ancien_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Ancien mot de passe incorrect.")
        return value

    def validate(self, attrs):
        if attrs["nouveau_password"] != attrs["nouveau_password2"]:
            raise serializers.ValidationError({"nouveau_password": "Les mots de passe ne correspondent pas."})
        return attrs

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["nouveau_password"])
        user.save()
        return user

class InscriptionSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = Utilisateur
        fields = ["username", "email", "nom", "prenom", "password", "password2"]

    def validate_email(self, value):
        value = normalize_email(value)
        if Utilisateur.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate(self, attrs):
        if Utilisateur.objects.filter(role="admin").exists():
            raise serializers.ValidationError({
                "detail": "Un compte administrateur existe déjà. Contactez votre administrateur pour obtenir un accès."
            })
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        if not attrs.get("email"):
            raise serializers.ValidationError({"email": "Email requis."})
        if Utilisateur.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "Ce nom d'utilisateur est déjà pris."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = Utilisateur(
            **validated_data,
            role="admin",  # toujours admin puisque l'inscription est bloquée sinon
            est_actif=False,
            email_verifie=False,
        )
        user.set_password(password)
        user.save()
        return user

class VerificationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = normalize_email(attrs["email"])
        try:
            user = Utilisateur.objects.get(email__iexact=email)
        except Utilisateur.DoesNotExist:
            raise serializers.ValidationError({"email": "Aucun compte avec cet email."})
        if user.email_verifie:
            raise serializers.ValidationError({"email": "Ce compte est déjà vérifié."})
        if not user.code_valide(attrs["code"]):
            raise serializers.ValidationError({"code": "Code invalide ou expiré."})
        attrs["_user"] = user
        attrs["email"] = email
        return attrs


class RenvoyerCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    motif = serializers.ChoiceField(choices=["verification", "reinitialisation"], default="verification")

    def validate(self, attrs):
        email = normalize_email(attrs["email"])
        try:
            user = Utilisateur.objects.get(email__iexact=email)
        except Utilisateur.DoesNotExist:
            raise serializers.ValidationError({"email": "Aucun compte avec cet email."})
        if attrs["motif"] == "verification" and user.email_verifie:
            raise serializers.ValidationError({"email": "Ce compte est déjà vérifié."})
        attrs["_user"] = user
        attrs["email"] = email
        return attrs


class DemandeReinitialisationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = normalize_email(value)
        if not Utilisateur.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Aucun compte avec cet email.")
        return value


class ReinitialiserMotDePasseSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    nouveau_password = serializers.CharField(write_only=True, validators=[validate_password])
    nouveau_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["nouveau_password"] != attrs["nouveau_password2"]:
            raise serializers.ValidationError({"nouveau_password": "Les mots de passe ne correspondent pas."})
        email = normalize_email(attrs["email"])
        try:
            user = Utilisateur.objects.get(email__iexact=email)
        except Utilisateur.DoesNotExist:
            raise serializers.ValidationError({"email": "Aucun compte avec cet email."})
        if not user.code_valide(attrs["code"]):
            raise serializers.ValidationError({"code": "Code invalide ou expiré."})
        attrs["_user"] = user
        attrs["email"] = email
        return attrs

class ModifierProfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ["nom", "prenom", "email"]

    def validate_email(self, value):
        value = normalize_email(value)
        user = self.instance
        if Utilisateur.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé par un autre compte.")
        return value