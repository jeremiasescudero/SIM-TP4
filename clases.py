class Alumno:
    def __init__(self, id, estado, maquina=None):
        self.id = id
        self.estado = estado
        self.recurso_asignado = None

    def asignar_recurso(self, recurso):
        self.recurso_asignado = recurso.nombre
        self.estado = "En proceso"


class Servidor:
    def __init__(self, nombre, tiempo_proceso):
        self.nombre = nombre
        self.libre = True
        self.tiempo_proceso = tiempo_proceso
        self.proximo_fin = None
