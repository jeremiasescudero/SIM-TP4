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
                        'proximo_mantenimiento': None,
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
        tiempo = 3 + (10 - 3) * rnd
        return rnd, round(tiempo, 2)

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
                # Inicializar tiempo de espera cuando entra en cola
                self.tiempos_espera[id_alumno] = 0
        else:
            anterior_estado = self.estado_alumnos[id_alumno]
            self.estado_alumnos[id_alumno] = estado
            
            if estado == EstadoAlumno.SIENDO_ATENDIDO and anterior_estado == EstadoAlumno.EN_COLA:
                self.alumnos_en_cola.remove(id_alumno)
                # Calcular tiempo total que estuvo en cola
                tiempo_espera = tiempo_actual - self.tiempo_llegada_alumnos[id_alumno]
                self.tiempos_espera[id_alumno] = tiempo_espera
                # Actualizar estadísticas
                self.tiempo_espera_total += tiempo_espera
                self.alumnos_con_espera += 1

    def calcular_tiempo_espera(self, id_alumno):
        if id_alumno in self.estado_alumnos:
            if self.estado_alumnos[id_alumno] == EstadoAlumno.EN_COLA:
                # Actualizar tiempo de espera en tiempo real mientras está en cola
                return round(self.tiempo_actual - self.tiempo_llegada_alumnos[id_alumno], 2)
            # Retornar tiempo final de espera si ya fue atendido
            return round(self.tiempos_espera.get(id_alumno, 0), 2)
        return 0

    def calcular_estadisticas_espera(self):
        if self.alumnos_con_espera > 0:
            acumulado = round(self.tiempo_espera_total, 2)  # Tiempo total acumulado
            promedio = round(acumulado / self.alumnos_con_espera, 2)  # Promedio solo de los que esperaron
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

        for i, equipo in enumerate(self.equipos, 1):
            estado_actual[f'Próximo Mant. M{i}'] = round(equipo['proximo_mantenimiento'], 2) if equipo['proximo_mantenimiento'] is not None else 'N/A'

    def obtener_proximo_evento(self):
        eventos = []
        
        # Agregar próxima llegada
        eventos.append(('llegada', self.proxima_llegada))
        
        # Agregar próximos mantenimientos y fines
        for equipo in self.equipos:
            if equipo['proximo_mantenimiento']:
                eventos.append(('inicio_mantenimiento', equipo['proximo_mantenimiento'], equipo))
            if equipo['fin_mantenimiento']:
                eventos.append(('fin_mantenimiento', equipo['fin_mantenimiento'], equipo))
            if equipo['fin_inscripcion']:
                eventos.append(('fin_inscripcion', equipo['fin_inscripcion'], equipo))
        
        if not eventos:
            return None
            
        # Ordenar eventos por tiempo y retornar el más próximo
        eventos.sort(key=lambda x: x[1])
        return eventos[0]

    def simular(self, tiempo_total):
        # Primera llegada
        rnd_llegada, tiempo_llegada = self.generar_tiempo_llegada()
        self.tiempo_actual = 0
        self.proxima_llegada = tiempo_llegada
        self.contador_alumnos = 1
        id_actual = f"A{self.contador_alumnos}"

        # Inicialización - Generar mantenimiento independiente para cada máquina
        for equipo in self.equipos:
            rnd_mant, tiempo_mant = self.generar_tiempo_mantenimiento()
            equipo['proximo_mantenimiento'] = tiempo_mant

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
            'RND Mantenimiento': 'N/A',
            'Tiempo Mantenimiento': 'N/A',
            'Fin Mantenimiento': 'N/A'
        }

        for i, equipo in enumerate(self.equipos, 1):
            estado[f'Máquina {i}'] = equipo['estado'].value
        estado['Cola'] = self.cola
        self.agregar_estados_alumnos(estado)
        self.resultados.append(estado)

        while self.tiempo_actual < tiempo_total:
            evento = self.obtener_proximo_evento()
            if not evento:
                break
                
            self.tiempo_actual = evento[1]
            tipo_evento = evento[0]

            if tipo_evento == 'llegada':
                estado = self.procesar_llegada(id_actual, rnd_llegada, tiempo_llegada)
                rnd_llegada, tiempo_llegada = self.generar_tiempo_llegada()
                self.proxima_llegada = self.tiempo_actual + tiempo_llegada
                self.contador_alumnos += 1
                id_actual = f"A{self.contador_alumnos}"
            
            elif tipo_evento == 'inicio_mantenimiento':
                equipo = evento[2]
                estado = self.procesar_inicio_mantenimiento(equipo)
            
            elif tipo_evento == 'fin_mantenimiento':
                equipo = evento[2]
                estado = self.procesar_fin_mantenimiento(equipo)
            
            elif tipo_evento == 'fin_inscripcion':
                equipo = evento[2]
                estado = self.procesar_fin_inscripcion(equipo)

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

    def procesar_inicio_mantenimiento(self, equipo):
        rnd_mant, tiempo_mant = self.generar_tiempo_mantenimiento()
        equipo['estado'] = EstadoEquipo.MANTENIMIENTO
        equipo['fin_mantenimiento'] = self.tiempo_actual + tiempo_mant
        equipo['proximo_mantenimiento'] = None

        estado = {
            'Evento': f'Inicio Mantenimiento M{equipo["id"]}',
            'Reloj': round(self.tiempo_actual, 2),
            'RND Llegada': 'N/A',
            'Tiempo Llegada': 'N/A',
            'Próxima Llegada': round(self.proxima_llegada, 2),
            'Máquina': equipo['id'],
            'RND Inscripción': 'N/A',
            'Tiempo Inscripción': 'N/A',
            'Fin Inscripción': 'N/A',
            'RND Mantenimiento': round(rnd_mant, 2),
            'Tiempo Mantenimiento': round(tiempo_mant, 2),
            'Fin Mantenimiento': round(equipo['fin_mantenimiento'], 2),
            'Cola': self.cola
        }

        for i, eq in enumerate(self.equipos, 1):
            estado[f'Máquina {i}'] = eq['estado'].value
        self.agregar_estados_alumnos(estado)
        return estado

    def procesar_fin_mantenimiento(self, equipo):
        equipo['estado'] = EstadoEquipo.LIBRE
        rnd_mant, tiempo_mant = self.generar_tiempo_mantenimiento()
        equipo['proximo_mantenimiento'] = self.tiempo_actual + tiempo_mant

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
            'RND Mantenimiento': round(rnd_mant, 2),
            'Tiempo Mantenimiento': round(tiempo_mant, 2),
            'Fin Mantenimiento': 'N/A',
            'Cola': self.cola
        }

        for i, eq in enumerate(self.equipos, 1):
            estado[f'Máquina {i}'] = eq['estado'].value
        self.agregar_estados_alumnos(estado)
        equipo['fin_mantenimiento'] = None
        return estado

    def procesar_fin_inscripcion(self, equipo):
        alumno_finalizado = equipo['alumno_actual']
        self.actualizar_estado_alumno(alumno_finalizado, EstadoAlumno.ATENCION_FINALIZADA, self.tiempo_actual)
        equipo['estado'] = EstadoEquipo.LIBRE

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
        
        if not self.alumnos_en_cola:
            equipo['fin_inscripcion'] = None
            equipo['alumno_actual'] = None
        
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


