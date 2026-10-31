from django.contrib.auth.password_validation import (
    CommonPasswordValidator,
    NumericPasswordValidator,
    UserAttributeSimilarityValidator,
)
from django.core.exceptions import ValidationError


class ValidadorSimilitud(UserAttributeSimilarityValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            raise ValidationError("La contraseña no debe parecerse a tus datos personales.")

    def get_help_text(self):
        return "La contraseña no debe parecerse a tus datos personales."


class ValidadorComun(CommonPasswordValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            raise ValidationError("La contraseña es demasiado común.")

    def get_help_text(self):
        return "La contraseña no puede ser una contraseña común."


class ValidadorNumerica(NumericPasswordValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            raise ValidationError("La contraseña no puede contener solo números.")

    def get_help_text(self):
        return "La contraseña no puede contener solo números."
