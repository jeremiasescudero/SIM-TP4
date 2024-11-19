import bisect
import random
from math import inf

class Evento:
    evento_id_counter = 1  # Contador global para IDs únicos de eventos

    def __init__(self, nombre, hora):
        self.id = Evento.evento_id_counter  # Asignar ID único al evento
        Evento.evento_id_counter += 1
        self.nombre = nombre
        self.hora = round(hora, 2)  # Capear a 2 decimales

    def __lt__(self, other):
        return self.hora < other.hora


class LlegadaAlumno(Evento):
    def __init__(self, hora, rnd_llegada, tiempo_llegada):
        super().__init__("Llegada Alumno", hora)
        self.rnd_llegada = round(rnd_llegada, 2)  # Capear a 2 decimales
        self.tiempo_llegada = round(tiempo_llegada, 2)  # Capear a 2 decimales

    def procesar(self, estado, eventos, alumnos, maquinas):
        # Generar próxima llegada
        rnd_llegada = round(random.random(), 2)
        tiempo_llegada = round(random.expovariate(1 / estado['media_llegada']), 2)
        nueva_llegada = LlegadaAlumno(
            hora=self.hora + tiempo_llegada,
            rnd_llegada=rnd_llegada,
            tiempo_llegada=tiempo_llegada
        )
        bisect.insort(eventos, nueva_llegada)

        # Registrar al alumno
        alumno = {'estado': 'En cola', 'hora_llegada': round(self.hora, 2), 'en_cola': True}
        alumnos.append(alumno)

        # Intentar asignarlo a una máquina
        for idx, maquina in enumerate(maquinas):
            if maquina['estado'] == 'Libre':
                rnd_inscripcion = round(random.random(), 2)
                tiempo_inscripcion = round(random.uniform(
                    estado['t_ins_min'], estado['t_ins_max']
                ), 2)
                fin_inscripcion = round(self.hora + tiempo_inscripcion, 2)
                maquina['estado'] = 'Ocupado'
                maquina['fin_inscripcion'] = fin_inscripcion
                alumno['estado'] = 'En inscripción'
                alumno['en_cola'] = False
                bisect.insort(eventos, FinInscripcion(fin_inscripcion, idx, rnd_inscripcion, tiempo_inscripcion))
                break

        return eventos


class ComienzoMantenimiento(Evento):
    def __init__(self, hora, maquina_id):
        super().__init__("Comienzo Mantenimiento", hora)
        self.maquina_id = maquina_id

    def procesar(self, estado, eventos, alumnos, maquinas):
        maquina = maquinas[self.maquina_id]
        rnd_mantenimiento = round(random.random(), 2)
        tiempo_mantenimiento = round(random.uniform(
            estado['t_mant_min'], estado['t_mant_max']
        ), 2)
        fin_mantenimiento = round(self.hora + tiempo_mantenimiento, 2)

        maquina['estado'] = 'En mantenimiento'
        maquina['fin_mantenimiento'] = fin_mantenimiento

        fin_evento = FinMantenimiento(fin_mantenimiento, self.maquina_id, rnd_mantenimiento, tiempo_mantenimiento)
        bisect.insort(eventos, fin_evento)

        return eventos


class FinInscripcion(Evento):
    def __init__(self, hora, maquina_id, rnd_inscripcion, tiempo_inscripcion):
        super().__init__("Fin Inscripción", hora)
        self.maquina_id = maquina_id
        self.rnd_inscripcion = round(rnd_inscripcion, 2)  # Capear a 2 decimales
        self.tiempo_inscripcion = round(tiempo_inscripcion, 2)  # Capear a 2 decimales

    def procesar(self, estado, eventos, alumnos, maquinas):
        maquina = maquinas[self.maquina_id]
        maquina['estado'] = 'Libre'
        maquina['fin_inscripcion'] = None
        return eventos


class FinMantenimiento(Evento):
    def __init__(self, hora, maquina_id, rnd_mantenimiento, tiempo_mantenimiento):
        super().__init__("Fin Mantenimiento", hora)
        self.maquina_id = maquina_id
        self.rnd_mantenimiento = round(rnd_mantenimiento, 2)  # Capear a 2 decimales
        self.tiempo_mantenimiento = round(tiempo_mantenimiento, 2)  # Capear a 2 decimales

    def procesar(self, estado, eventos, alumnos, maquinas):
        maquina = maquinas[self.maquina_id]
        maquina['estado'] = 'Libre'
        maquina['fin_mantenimiento'] = None

        # Programar próximo mantenimiento
        proximo_mantenimiento = round(self.hora + estado['mant_intervalo'], 2)
        bisect.insort(eventos, ComienzoMantenimiento(proximo_mantenimiento, self.maquina_id))

        return eventos


def simular(
    media_llegada, t_ins_min, t_ins_max, t_mant_min, t_mant_max,
    mant_intervalo, dias_simulacion, equipos, inf_inscripcion,
    sup_inscripcion, mant_desviacion, max_cola, tiempo_retorno
):
    # Inicialización
    estado = {
        'media_llegada': media_llegada,
        't_ins_min': t_ins_min,
        't_ins_max': t_ins_max,
        't_mant_min': t_mant_min,
        't_mant_max': t_mant_max,
        'mant_intervalo': mant_intervalo,
        'mant_desviacion': mant_desviacion,
        'equipos': equipos,
        'inf_inscripcion': inf_inscripcion,
        'sup_inscripcion': sup_inscripcion,
        'max_cola': max_cola,
        'tiempo_retorno': tiempo_retorno,
    }
    reloj = 0
    eventos = []
    alumnos = []
    maquinas = [{'estado': 'Libre', 'fin_inscripcion': None, 'fin_mantenimiento': None} for _ in range(equipos)]
    tabla_resultados = []

    # Evento inicial: primera llegada de alumno
    rnd_llegada = round(random.random(), 2)
    tiempo_llegada = round(random.expovariate(1 / media_llegada), 2)
    primera_llegada = LlegadaAlumno(
        hora=tiempo_llegada,
        rnd_llegada=rnd_llegada,
        tiempo_llegada=tiempo_llegada
    )
    bisect.insort(eventos, primera_llegada)

    # Evento inicial: primer mantenimiento por máquina
    for i in range(equipos):
        bisect.insort(eventos, ComienzoMantenimiento(hora=mant_intervalo, maquina_id=i))

    # Ciclo de simulación
    while reloj < dias_simulacion * 24 * 60 and eventos:
        evento_actual = eventos.pop(0)
        reloj = evento_actual.hora
        eventos = evento_actual.procesar(estado, eventos, alumnos, maquinas)

        # Registrar estado del sistema
        fila = {
            'ID Evento': evento_actual.id,
            'Evento': evento_actual.nombre,
            'Reloj': round(reloj, 2),
            'Cola': len([alumno for alumno in alumnos if alumno['estado'] == 'En cola']),
        }

        # Añadir datos para cada alumno dinámicamente
        for idx, alumno in enumerate(alumnos, start=1):
            fila[f'A{idx}'] = {
                'Estado': alumno['estado'],
                'Tiempo de Espera': round(reloj - alumno['hora_llegada'], 2) if alumno['estado'] == 'En cola' else 0
            }

        # Añadir datos de eventos (llegadas, inscripciones, mantenimientos)
        fila.update({
            'RND Llegada': getattr(evento_actual, 'rnd_llegada', 'N/A'),
            'Tiempo Llegada': getattr(evento_actual, 'tiempo_llegada', 'N/A'),
            'Próxima Llegada': round(eventos[0].hora, 2) if eventos else 'N/A',
            'Máquina': getattr(evento_actual, 'maquina_id', 'N/A'),
            'RND Inscripción': getattr(evento_actual, 'rnd_inscripcion', 'N/A'),
            'Tiempo Inscripción': getattr(evento_actual, 'tiempo_inscripcion', 'N/A'),
            'Fin Inscripción': getattr(evento_actual, 'hora', 'N/A'),
            'RND Mantenimiento': getattr(evento_actual, 'rnd_mantenimiento', 'N/A'),
            'Tiempo Mantenimiento': getattr(evento_actual, 'tiempo_mantenimiento', 'N/A'),
            'Fin Mantenimiento': getattr(evento_actual, 'hora', 'N/A'),
        })

        tabla_resultados.append(fila)

    return tabla_resultados, len(alumnos), equipos
