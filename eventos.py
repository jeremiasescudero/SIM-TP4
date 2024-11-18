import random
from utils import *
from clases import *

class Evento:
    def __init__(self, hora):
        self.nombre = "Evento"
        self.hora = hora

    def make(self, estadisticas):
        estadisticas['reloj'] = self.hora


class InicioSimulacion(Evento):
    def __init__(self):
        super().__init__(0)
        self.nombre = "Inicio de Simulación"

    def make(self, estadisticas, eventos, objetos_temporales, recursos):
        super().make(estadisticas)
        estadisticas['contador_eventos'] = 0
        estadisticas['max_cola'] = 0
        objetos_temporales.clear()

        primer_evento = Llegada(estadisticas['rango_llegada'], estadisticas['reloj'])
        return primer_evento, None, None


class Llegada(Evento):
    def __init__(self, rango, reloj):
        self.rnd_llegada = truncate(random.random())
        self.tiempo = calcular_uniforme(self.rnd_llegada, rango)
        super().__init__(reloj + self.tiempo)
        self.nombre = "Llegada de Objeto"

    def make(self, estadisticas, eventos, objetos_temporales, recursos):
        super().make(estadisticas)
        estadisticas['contador_eventos'] += 1
        nuevo_objeto = ObjetoTemporal(estadisticas['contador_eventos'])
        objetos_temporales.append(nuevo_objeto)

        recurso_disponible = next((recurso for recurso in recursos if recurso.libre), None)
        fin_proceso = None

        if recurso_disponible:
            recurso_disponible.libre = False
            nuevo_objeto.asignar_recurso(recurso_disponible)
            fin_proceso = FinProceso(estadisticas['reloj'], nuevo_objeto, recurso_disponible)
        else:
            estadisticas['cola'] += 1
            nuevo_objeto.estado = "En cola"

        proxima_llegada = Llegada(estadisticas['rango_llegada'], estadisticas['reloj'])
        return proxima_llegada, fin_proceso, None


class FinProceso(Evento):
    def __init__(self, reloj, objeto, recurso):
        self.rnd_proceso = truncate(random.random())
        self.tiempo = calcular_uniforme(self.rnd_proceso, recurso.tiempo_proceso)
        super().__init__(reloj + self.tiempo)
        self.nombre = "Fin de Proceso"
        self.objeto = objeto
        self.recurso = recurso

    def make(self, estadisticas, eventos, objetos_temporales, recursos):
        super().make(estadisticas)
        self.objeto.estado = "Procesado"
        self.recurso.libre = True

        fin_proceso = None
        if estadisticas['cola'] > 0:
            objeto_en_cola = next((obj for obj in objetos_temporales if obj.estado == "En cola"), None)
            if objeto_en_cola:
                objeto_en_cola.asignar_recurso(self.recurso)
                fin_proceso = FinProceso(estadisticas['reloj'], objeto_en_cola, self.recurso)
                objeto_en_cola.estado = "En proceso"
                estadisticas['cola'] -= 1

        return None, fin_proceso, None
