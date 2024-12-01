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
                        'fin_inscripcion': None} for i in range(equipos)]
        self.inf_inscripcion = inf_inscripcion
        self.sup_inscripcion = sup_inscripcion
        self.media_llegada = media_llegada
        self.cola = 0
        self.tiempo_actual = 0
        self.resultados = []
        self.contador_alumnos = 0

    def generar_tiempo_llegada(self):
        rnd = random.random()
        tiempo = -self.media_llegada * math.log(1 - rnd)
        return rnd, round(tiempo, 2)

    def generar_tiempo_inscripcion(self):
        rnd = random.random()
        tiempo = self.inf_inscripcion + (self.sup_inscripcion - self.inf_inscripcion) * rnd
        return rnd, round(tiempo, 2)

    def obtener_equipo_libre(self):
        for equipo in self.equipos:
            if equipo['estado'] == EstadoEquipo.LIBRE:
                return equipo
        return None

    def simular(self, tiempo_total):
        # Primera llegada
        rnd_llegada, tiempo_llegada = self.generar_tiempo_llegada()
        proxima_llegada = tiempo_llegada
        self.contador_alumnos += 1
        id_actual = f"A{self.contador_alumnos}"

        while self.tiempo_actual < tiempo_total:
            estado = {
                'Evento': f'Llegada Alumno {id_actual}',
                'Reloj': round(self.tiempo_actual, 2),
                'RND Llegada': round(rnd_llegada, 2),
                'Tiempo Llegada': round(tiempo_llegada, 2),
                'Próxima Llegada': round(proxima_llegada, 2),
                'Máquina': 'N/A',
                'RND Inscripción': 'N/A',
                'Tiempo Inscripción': 'N/A',
                'Fin Inscripción': 'N/A',
                'RND Mantenimiento': 'N/A',
                'Tiempo Mantenimiento': 'N/A',
                'Fin Mantenimiento': 'N/A'
            }

            # Procesar llegada
            equipo_libre = self.obtener_equipo_libre()
            if equipo_libre:
                equipo_libre['estado'] = EstadoEquipo.OCUPADO
                rnd_ins, tiempo_ins = self.generar_tiempo_inscripcion()
                equipo_libre['fin_inscripcion'] = self.tiempo_actual + tiempo_ins
                equipo_libre['alumno_actual'] = id_actual
                estado.update({
                    'Máquina': equipo_libre['id'],
                    'RND Inscripción': round(rnd_ins, 2),
                    'Tiempo Inscripción': round(tiempo_ins, 2),
                    'Fin Inscripción': round(equipo_libre['fin_inscripcion'], 2)
                })
            else:
                self.cola += 1

            # Actualizar estado de equipos
            for i, equipo in enumerate(self.equipos, 1):
                estado[f'Máquina {i}'] = equipo['estado'].value

            estado['Cola'] = self.cola
            self.resultados.append(estado)

            # Verificar fin de inscripciones
            for equipo in self.equipos:
                if (equipo['estado'] == EstadoEquipo.OCUPADO and 
                    equipo['fin_inscripcion'] and 
                    equipo['fin_inscripcion'] <= proxima_llegada):
                    self.resultados.append({
                        'Evento': f'Fin Inscripción {equipo["alumno_actual"]}',
                        'Reloj': round(equipo['fin_inscripcion'], 2),
                        'RND Llegada': 'N/A',
                        'Tiempo Llegada': 'N/A',
                        'Próxima Llegada': round(proxima_llegada, 2),
                        'Máquina': equipo['id'],
                        'RND Inscripción': 'N/A',
                        'Tiempo Inscripción': 'N/A',
                        'Fin Inscripción': round(equipo['fin_inscripcion'], 2),
                        'RND Mantenimiento': 'N/A',
                        'Tiempo Mantenimiento': 'N/A',
                        'Fin Mantenimiento': 'N/A',
                        'Cola': self.cola
                    })
                    equipo['estado'] = EstadoEquipo.LIBRE
                    equipo['fin_inscripcion'] = None
                    equipo['alumno_actual'] = None
                    if self.cola > 0:
                        self.cola -= 1

            self.tiempo_actual = proxima_llegada
            rnd_llegada, tiempo_llegada = self.generar_tiempo_llegada()
            proxima_llegada = self.tiempo_actual + tiempo_llegada
            self.contador_alumnos += 1
            id_actual = f"A{self.contador_alumnos}"

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