from core.permissions import puede_ver_finanzas


def permisos_finanzas(request):
    return {"puede_ver_finanzas": puede_ver_finanzas(request.user)}
