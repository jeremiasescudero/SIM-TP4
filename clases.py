class ObjetoTemporal:
    def __init__(self, id):
        self.id = id
        self.estado = "Inicial"
        self.recurso_asignado = None

    def asignar_recurso(self, recurso):
        self.recurso_asignado = recurso.nombre
        self.estado = "En proceso"


class Recurso:
    def __init__(self, nombre, tiempo_proceso):
        self.nombre = nombre
        self.libre = True
        self.tiempo_proceso = tiempo_proceso
