from .models import ConfiguracionRegistro


def registro_habilitado(request):
    config = ConfiguracionRegistro.singleton()
    return {"registro_habilitado": config.registro_habilitado}
