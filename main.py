import os
import random
import math
from flask import Flask, request, render_template
from enum import Enum

class EstadoEquipo(Enum):
    LIBRE = "Libre"
    OCUPADO = "Ocupado"
    MANTENIMIENTO = "Mantenimiento"

class EstadoAlumno(Enum):
    SIENDO_ATENDIDO = "SA"
    EN_COLA = "EC"
    ATENCION_FINALIZADA = "AF"

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates_new'))

class Simulacion:
    def __init__(self, equipos=6, inf_inscripcion=5, sup_inscripcion=8, media_llegada=2.0):
        self.equipos = [{'id': i+1, 
                        'estado': EstadoEquipo.LIBRE, 
                        'fin_inscripcion': None,
                        'fin_mantenimiento': None,
                        'alumno_actual': None} for i in range(equipos)]
        self.inf_inscripcion = inf_inscripcion
        self.sup_inscripcion = sup_inscripcion
        self.media_llegada = media_llegada
        self.cola = 0
        self.tiempo_actual = 0
        self.resultados = []
        self.contador_alumnos = 0
        self.estado_alumnos = {}
        self.tiempo_llegada_alumnos = {}
        self.tiempo_inicio_atencion = {}
        self.tiempos_espera = {}
        self.alumnos_en_cola = []
        self.tiempo_espera_total = 0
        self.alumnos_con_espera = 0
        self.proximo_mantenimiento = None
        self.mantenimiento_en_espera = False

        self.proxima_computadora_mantenimiento = 0

    def generar_tiempo_llegada(self):
        rnd = random.random()
        tiempo = -self.media_llegada * math.log(1 - rnd)
        return rnd, round(tiempo, 2)

    def generar_tiempo_inscripcion(self):
        rnd = random.random()
        tiempo = self.inf_inscripcion + (self.sup_inscripcion - self.inf_inscripcion) * rnd
        return rnd, round(tiempo, 2)

    def generar_tiempo_mantenimiento(self):
        rnd = random.random()
        tiempo = 3 + (10 - 3) * rnd  # Duración del mantenimiento: U(3,10) minutos
        return rnd, round(tiempo, 2)

    def generar_tiempo_regreso(self):
        rnd = random.random()
        tiempo = 57 + (63 - 57) * rnd  # Tiempo hasta próximo mantenimiento: U(57,63) minutos
        return rnd, round(tiempo, 2)

    def generar_tiempo_regreso(self):
        rnd = random.random()
        tiempo_regreso = 57 + (63 - 57) * rnd  # Tiempo hasta próximo mantenimiento: U(57,63) minutos
        return rnd, round(tiempo_regreso, 2)

    def obtener_equipo_libre(self):
        for equipo in self.equipos:
            if equipo['estado'] == EstadoEquipo.LIBRE:
                return equipo
        return None

    def actualizar_estado_alumno(self, id_alumno, estado, tiempo_actual):
        if id_alumno not in self.estado_alumnos:
            self.estado_alumnos[id_alumno] = estado
            self.tiempo_llegada_alumnos[id_alumno] = tiempo_actual
            if estado == EstadoAlumno.EN_COLA:
                self.alumnos_en_cola.append(id_alumno)
                self.tiempos_espera[id_alumno] = 0
                # Agregar el alumno al conteo de espera inmediatamente
                self.alumnos_con_espera += 1
        else:
            anterior_estado = self.estado_alumnos[id_alumno]
            self.estado_alumnos[id_alumno] = estado
            
            if estado == EstadoAlumno.SIENDO_ATENDIDO and anterior_estado == EstadoAlumno.EN_COLA:
                self.alumnos_en_cola.remove(id_alumno)
                tiempo_espera = tiempo_actual - self.tiempo_llegada_alumnos[id_alumno]
                self.tiempos_espera[id_alumno] = tiempo_espera
                if tiempo_espera > 0:
                    self.tiempo_espera_total += tiempo_espera

    def calcular_tiempo_espera(self, id_alumno):
        if id_alumno in self.estado_alumnos:
            if self.estado_alumnos[id_alumno] == EstadoAlumno.EN_COLA:
                tiempo_espera = self.tiempo_actual - self.tiempo_llegada_alumnos[id_alumno]
                # Actualizar el tiempo total acumulado
                self.tiempo_espera_total += tiempo_espera
                return round(tiempo_espera, 2)
            return round(self.tiempos_espera.get(id_alumno, 0), 2)
        return 0

    def calcular_estadisticas_espera(self):
        if self.alumnos_con_espera > 0:
            acumulado = round(self.tiempo_espera_total, 2)
            promedio = round(acumulado / self.alumnos_con_espera, 2)
            return acumulado, promedio
        return 0, 0

    def agregar_estados_alumnos(self, estado_actual):
        for i in range(1, self.contador_alumnos + 1):
            alumno_id = f"A{i}"
            if alumno_id in self.estado_alumnos:
                estado_actual[f'Estado {alumno_id}'] = self.estado_alumnos[alumno_id].value
                estado_actual[f'Tiempo Espera {alumno_id}'] = self.calcular_tiempo_espera(alumno_id)
        
        acumulado, promedio = self.calcular_estadisticas_espera()
        estado_actual['Tiempo Espera Acumulado'] = acumulado
        estado_actual['Tiempo Espera Promedio'] = promedio

    def obtener_proximo_evento(self):
        eventos = []
        eventos.append(('llegada', self.proxima_llegada))
        
        if self.proximo_mantenimiento and not self.mantenimiento_en_espera:
            eventos.append(('inicio_mantenimiento', self.proximo_mantenimiento))
            
        for equipo in self.equipos:
            if equipo['fin_mantenimiento']:
                eventos.append(('fin_mantenimiento', equipo['fin_mantenimiento'], equipo))
            if equipo['fin_inscripcion']:
                eventos.append(('fin_inscripcion', equipo['fin_inscripcion'], equipo))
        
        eventos.sort(key=lambda x: x[1])
        return eventos[0]

    def simular(self, tiempo_total):
        rnd_llegada, tiempo_llegada = self.generar_tiempo_llegada()
        self.tiempo_actual = 0
        self.proxima_llegada = tiempo_llegada
        self.contador_alumnos = 1
        id_actual = f"A{self.contador_alumnos}"

        # Inicialización - Generar primer mantenimiento
        """rnd_mant, tiempo_mant = self.generar_tiempo_mantenimiento()
        self.proximo_mantenimiento = tiempo_mant"""

        rnd_mant, tiempo_mant = self.generar_tiempo_mantenimiento()
        self.equipos[0]['estado'] = EstadoEquipo.MANTENIMIENTO
        self.equipos[0]['fin_mantenimiento'] = tiempo_mant
        self.proxima_computadora_mantenimiento = 1

        estado = {
            'Evento': 'Inicializacion',
            'Reloj': round(self.tiempo_actual, 2),
            'RND Llegada': round(rnd_llegada, 2),
            'Tiempo Llegada': round(tiempo_llegada, 2),
            'Próxima Llegada': round(self.proxima_llegada, 2),
            'Máquina': 'N/A',
            'RND Inscripción': 'N/A',
            'Tiempo Inscripción': 'N/A',
            'Fin Inscripción': 'N/A',
            'RND Mantenimiento': round(rnd_mant, 2),
            'Tiempo Mantenimiento': round(tiempo_mant, 2),
            'Fin Mantenimiento': round(tiempo_mant, 2)
            #'Fin Mantenimiento': 'N/A'
        }

        for i, equipo in enumerate(self.equipos, 1):
            estado[f'Máquina {i}'] = equipo['estado'].value
        estado['Cola'] = self.cola
        self.agregar_estados_alumnos(estado)
        self.resultados.append(estado)

        while self.tiempo_actual < tiempo_total:
            evento = self.obtener_proximo_evento()
            self.tiempo_actual = evento[1]
            tipo_evento = evento[0]

            if tipo_evento == 'llegada':
                estado = self.procesar_llegada(id_actual, rnd_llegada, tiempo_llegada)
                rnd_llegada, tiempo_llegada = self.generar_tiempo_llegada()
                self.proxima_llegada = self.tiempo_actual + tiempo_llegada
                self.contador_alumnos += 1
                id_actual = f"A{self.contador_alumnos}"
            
            elif tipo_evento == 'inicio_mantenimiento':
                estado = self.procesar_inicio_mantenimiento()
                if estado is None:
                    continue
            
            elif tipo_evento == 'fin_mantenimiento':
                equipo = evento[2]
                estado = self.procesar_fin_mantenimiento(equipo)
            
            elif tipo_evento == 'fin_inscripcion':
                equipo = evento[2]
                estado = self.procesar_fin_inscripcion(equipo)

            if estado:
                self.resultados.append(estado)

        for estado in self.resultados:
            estado['max_alumnos'] = self.contador_alumnos

        return sorted(self.resultados, key=lambda x: x['Reloj'])

    def procesar_llegada(self, id_alumno, rnd_llegada, tiempo_llegada):
        estado = {
            'Evento': f'Llegada Alumno {id_alumno}',
            'Reloj': round(self.tiempo_actual, 2),
            'RND Llegada': round(rnd_llegada, 2),
            'Tiempo Llegada': round(tiempo_llegada, 2),
            'Próxima Llegada': round(self.proxima_llegada, 2),
            'Máquina': 'N/A',
            'RND Inscripción': 'N/A',
            'Tiempo Inscripción': 'N/A',
            'Fin Inscripción': 'N/A',
            'RND Mantenimiento': 'N/A',
            'Tiempo Mantenimiento': 'N/A',
            'Fin Mantenimiento': 'N/A'
        }

        equipo_libre = self.obtener_equipo_libre()
        if equipo_libre:
            equipo_libre['estado'] = EstadoEquipo.OCUPADO
            rnd_ins, tiempo_ins = self.generar_tiempo_inscripcion()
            equipo_libre['fin_inscripcion'] = self.tiempo_actual + tiempo_ins
            equipo_libre['alumno_actual'] = id_alumno
            estado.update({
                'Máquina': equipo_libre['id'],
                'RND Inscripción': round(rnd_ins, 2),
                'Tiempo Inscripción': round(tiempo_ins, 2),
                'Fin Inscripción': round(equipo_libre['fin_inscripcion'], 2)
            })
            self.actualizar_estado_alumno(id_alumno, EstadoAlumno.SIENDO_ATENDIDO, self.tiempo_actual)
        else:
            self.cola += 1
            self.actualizar_estado_alumno(id_alumno, EstadoAlumno.EN_COLA, self.tiempo_actual)

        for i, equipo in enumerate(self.equipos, 1):
            estado[f'Máquina {i}'] = equipo['estado'].value
        estado['Cola'] = self.cola
        self.agregar_estados_alumnos(estado)
        return estado

    def procesar_inicio_mantenimiento(self):
    # Si hay mantenimiento en espera, no generar nuevo evento
        if self.mantenimiento_en_espera:
            return None
            
        equipo_libre = self.obtener_equipo_libre()
        if not equipo_libre:
            self.mantenimiento_en_espera = True
            return None

        rnd_mant, tiempo_mant = self.generar_tiempo_mantenimiento()
        equipo_libre['estado'] = EstadoEquipo.MANTENIMIENTO
        equipo_libre['fin_mantenimiento'] = self.tiempo_actual + tiempo_mant
        self.proximo_mantenimiento = None

        estado = {
            'Evento': f'Inicio Mantenimiento M{equipo_libre["id"]}',
            'Reloj': round(self.tiempo_actual, 2),
            'RND Llegada': 'N/A',
            'Tiempo Llegada': 'N/A',
            'Próxima Llegada': round(self.proxima_llegada, 2),
            'Máquina': equipo_libre['id'],
            'RND Inscripción': 'N/A',
            'Tiempo Inscripción': 'N/A',
            'Fin Inscripción': 'N/A',
            'RND Mantenimiento': round(rnd_mant, 2),
            'Tiempo Mantenimiento': round(tiempo_mant, 2),
            'Fin Mantenimiento': round(equipo_libre['fin_mantenimiento'], 2),
            'Cola': self.cola
        }

        for i, eq in enumerate(self.equipos, 1):
            estado[f'Máquina {i}'] = eq['estado'].value
        self.agregar_estados_alumnos(estado)
        return estado

    def procesar_fin_mantenimiento(self, equipo):
        equipo['estado'] = EstadoEquipo.LIBRE
        equipo['fin_mantenimiento'] = None
        
        # Generar el tiempo para el próximo regreso del técnico
        #rnd_regreso, tiempo_regreso = self.generar_tiempo_regreso()
        #self.proximo_mantenimiento = self.tiempo_actual + tiempo_regreso
        #self.mantenimiento_en_espera = False

        estado = {
            'Evento': f'Fin Mantenimiento M{equipo["id"]}',
            'Reloj': round(self.tiempo_actual, 2),
            'RND Llegada': 'N/A',
            'Tiempo Llegada': 'N/A',
            'Próxima Llegada': round(self.proxima_llegada, 2),
            'Máquina': equipo['id'],
            'RND Inscripción': 'N/A',
            'Tiempo Inscripción': 'N/A',
            'Fin Inscripción': 'N/A',
            #'RND Mantenimiento': round(rnd_regreso, 2),
            #'Tiempo Mantenimiento': round(tiempo_regreso, 2),
            'RND Mantenimiento': 'N/A',
            'Tiempo Mantenimiento': 'N/A',
            'Fin Mantenimiento': 'N/A',
            'Cola': self.cola
        }

        # Iniciar mantenimiento de la siguiente computadora
        if self.proxima_computadora_mantenimiento < len(self.equipos):
            siguiente_equipo = self.equipos[self.proxima_computadora_mantenimiento]
            rnd_mant, tiempo_mant = self.generar_tiempo_mantenimiento()
            siguiente_equipo['estado'] = EstadoEquipo.MANTENIMIENTO
            siguiente_equipo['fin_mantenimiento'] = self.tiempo_actual + tiempo_mant
            self.proxima_computadora_mantenimiento += 1

            estado['Máquina'] = siguiente_equipo['id']
            estado['RND Mantenimiento'] = round(rnd_mant, 2)
            estado['Tiempo Mantenimiento'] = round(tiempo_mant, 2)
            estado['Fin Mantenimiento'] = round(siguiente_equipo['fin_mantenimiento'], 2)

        for i, eq in enumerate(self.equipos, 1):
            estado[f'Máquina {i}'] = eq['estado'].value
        self.agregar_estados_alumnos(estado)

        # Si hay alumnos en cola, atender al siguiente
        if self.alumnos_en_cola:
            siguiente_alumno = self.alumnos_en_cola[0]
            rnd_ins, tiempo_ins = self.generar_tiempo_inscripcion()
            equipo['estado'] = EstadoEquipo.OCUPADO
            equipo['fin_inscripcion'] = self.tiempo_actual + tiempo_ins
            equipo['alumno_actual'] = siguiente_alumno
            self.actualizar_estado_alumno(siguiente_alumno, EstadoAlumno.SIENDO_ATENDIDO, self.tiempo_actual)
            self.cola -= 1

        return estado

    def procesar_fin_inscripcion(self, equipo):
        alumno_finalizado = equipo['alumno_actual']
        self.actualizar_estado_alumno(alumno_finalizado, EstadoAlumno.ATENCION_FINALIZADA, self.tiempo_actual)
        equipo['estado'] = EstadoEquipo.LIBRE
        equipo['fin_inscripcion'] = None
        equipo['alumno_actual'] = None

        # Atender siguiente alumno en cola si existe
        if self.alumnos_en_cola:
            siguiente_alumno = self.alumnos_en_cola[0]
            rnd_ins, tiempo_ins = self.generar_tiempo_inscripcion()
            equipo['estado'] = EstadoEquipo.OCUPADO
            equipo['fin_inscripcion'] = self.tiempo_actual + tiempo_ins
            equipo['alumno_actual'] = siguiente_alumno
            self.actualizar_estado_alumno(siguiente_alumno, EstadoAlumno.SIENDO_ATENDIDO, self.tiempo_actual)
            self.cola -= 1

        estado = {
            'Evento': f'Fin Inscripción {alumno_finalizado}',
            'Reloj': round(self.tiempo_actual, 2),
            'RND Llegada': 'N/A',
            'Tiempo Llegada': 'N/A',
            'Próxima Llegada': round(self.proxima_llegada, 2),
            'Máquina': equipo['id'],
            'RND Inscripción': 'N/A' if not self.alumnos_en_cola else round(rnd_ins, 2),
            'Tiempo Inscripción': 'N/A' if not self.alumnos_en_cola else round(tiempo_ins, 2),
            'Fin Inscripción': 'N/A' if not self.alumnos_en_cola else round(equipo['fin_inscripcion'], 2),
            'RND Mantenimiento': 'N/A',
            'Tiempo Mantenimiento': 'N/A',
            'Fin Mantenimiento': 'N/A',
            'Cola': self.cola
        }

        for i, eq in enumerate(self.equipos, 1):
            estado[f'Máquina {i}'] = eq['estado'].value
        self.agregar_estados_alumnos(estado)

        return estado

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        sim = Simulacion()
        tabla = sim.simular(480)  # 8 horas
        return render_template('nuevo_colas.html', tabla=tabla)
    return render_template('menu.html')

if __name__ == '__main__':
    app.run(debug=True)