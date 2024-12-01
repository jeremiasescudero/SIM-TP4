import os
import random
import math
from flask import Flask, request, render_template
from enum import Enum

class EstadoEquipo(Enum):
    LIBRE = "Libre"
    OCUPADO = "Ocupado"
    MANTENIMIENTO = "Mantenimiento"

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates_new'))

class Simulacion:
    def __init__(self, equipos=6, inf_inscripcion=5, sup_inscripcion=8, media_llegada=2.0):
        self.equipos = [{'id': i+1, 'estado': EstadoEquipo.LIBRE, 
                        'fin_inscripcion': None,
                        'fin_mantenimiento': None} for i in range(equipos)]
        self.inf_inscripcion = inf_inscripcion
        self.sup_inscripcion = sup_inscripcion
        self.media_llegada = media_llegada
        self.cola = 0
        self.tiempo_actual = 0
        self.resultados = []
        self.proximo_mantenimiento = 60

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

    def simular(self, tiempo_total):
        # Primera llegada
        rnd_llegada, tiempo_llegada = self.generar_tiempo_llegada()
        self.tiempo_actual = tiempo_llegada
        proxima_llegada = self.tiempo_actual + tiempo_llegada
        max_iteraciones = 10000  # Límite de seguridad
        iteracion = 0

        while self.tiempo_actual < tiempo_total and iteracion < max_iteraciones:
            iteracion += 1
            eventos = []
            
            # Recolectar todos los eventos posibles
            eventos.append(('Llegada Alumno', proxima_llegada))
            
            # Verificar mantenimiento
            if self.tiempo_actual >= self.proximo_mantenimiento:
                eventos.append(('Inicio Mantenimiento', self.tiempo_actual))
            
            # Verificar fin de inscripciones y mantenimientos
            for equipo in self.equipos:
                if equipo['fin_inscripcion'] and equipo['fin_inscripcion'] <= proxima_llegada:
                    eventos.append(('Fin Inscripción', equipo['fin_inscripcion'], equipo['id']))
                if equipo['fin_mantenimiento'] and equipo['fin_mantenimiento'] <= proxima_llegada:
                    eventos.append(('Fin Mantenimiento', equipo['fin_mantenimiento'], equipo['id']))

            # Obtener el evento más próximo
            evento = min(eventos, key=lambda x: x[1])
            self.tiempo_actual = evento[1]
            
            estado = {
                'Evento': evento[0],
                'Reloj': round(self.tiempo_actual, 2),
                'RND Llegada': 'N/A',
                'Tiempo Llegada': 'N/A',
                'Próxima Llegada': round(proxima_llegada, 2),
                'Máquina': 'N/A',
                'RND Inscripción': 'N/A',
                'Tiempo Inscripción': 'N/A',
                'Fin Inscripción': 'N/A',
                'RND Mantenimiento': 'N/A',
                'Tiempo Mantenimiento': 'N/A',
                'Fin Mantenimiento': 'N/A'
            }

            # Procesar el evento según su tipo
            if evento[0] == 'Llegada Alumno':
                estado.update({
                    'RND Llegada': round(rnd_llegada, 2),
                    'Tiempo Llegada': round(tiempo_llegada, 2)
                })
                equipo_libre = self.obtener_equipo_libre()
                if equipo_libre:
                    rnd_ins, tiempo_ins = self.generar_tiempo_inscripcion()
                    equipo_libre['estado'] = EstadoEquipo.OCUPADO
                    equipo_libre['fin_inscripcion'] = self.tiempo_actual + tiempo_ins
                    estado.update({
                        'Máquina': equipo_libre['id'],
                        'RND Inscripción': round(rnd_ins, 2),
                        'Tiempo Inscripción': round(tiempo_ins, 2),
                        'Fin Inscripción': round(equipo_libre['fin_inscripcion'], 2)
                    })
                else:
                    self.cola += 1
                rnd_llegada, tiempo_llegada = self.generar_tiempo_llegada()
                proxima_llegada = self.tiempo_actual + tiempo_llegada

            elif evento[0] == 'Inicio Mantenimiento':
                equipo_libre = self.obtener_equipo_libre()
                if equipo_libre:
                    rnd_mant, tiempo_mant = self.generar_tiempo_mantenimiento()
                    equipo_libre['estado'] = EstadoEquipo.MANTENIMIENTO
                    equipo_libre['fin_mantenimiento'] = self.tiempo_actual + tiempo_mant
                    estado.update({
                        'Máquina': equipo_libre['id'],
                        'RND Mantenimiento': round(rnd_mant, 2),
                        'Tiempo Mantenimiento': round(tiempo_mant, 2),
                        'Fin Mantenimiento': round(equipo_libre['fin_mantenimiento'], 2)
                    })
                self.proximo_mantenimiento += 60

            elif evento[0] in ['Fin Inscripción', 'Fin Mantenimiento']:
                equipo_id = evento[2]
                equipo = next(eq for eq in self.equipos if eq['id'] == equipo_id)
                equipo['estado'] = EstadoEquipo.LIBRE
                if evento[0] == 'Fin Inscripción':
                    equipo['fin_inscripcion'] = None
                    if self.cola > 0:
                        self.cola -= 1
                else:
                    equipo['fin_mantenimiento'] = None

            # Actualizar estado de equipos
            for i, equipo in enumerate(self.equipos, 1):
                estado[f'Máquina {i}'] = equipo['estado'].value

            estado['Cola'] = self.cola
            self.resultados.append(estado)

        return sorted(self.resultados, key=lambda x: x['Reloj'])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        sim = Simulacion()
        tabla = sim.simular(480)  # 8 horas
        return render_template('nuevo_colas.html', tabla=tabla)
    return render_template('menu.html')

if __name__ == '__main__':
    app.run(debug=True)