import random


def simular(equipos, inf_inscripcion, sup_inscripcion, media_llegada, mant_min, mant_max, mant_intervalo, mant_desviacion, max_cola, tiempo_retorno):
    tiempo_actual = 0
    cola = []
    alumnos_atendidos = []
    alumnos_se_fueron = 0
    equipos_estado = [{'estado': 'Libre', 'fin_atencion': 0, 'alumno': None} for _ in range(equipos)]
    tabla_simulacion = []

    alumno_id = 1  # Identificador único para cada alumno

    while tiempo_actual < mant_intervalo:
        # Generar la llegada del próximo alumno
        tiempo_llegada = random.expovariate(1 / media_llegada)
        tiempo_actual += tiempo_llegada

        # Registrar llegada del alumno
        if len(cola) < max_cola:
            cola.append({'id': alumno_id, 'llegada': tiempo_actual})
        else:
            alumnos_se_fueron += 1

        # Actualizar estados de los equipos
        for equipo in equipos_estado:
            if equipo['estado'] == 'Ocupado' and equipo['fin_atencion'] <= tiempo_actual:
                # Liberar equipo
                equipo['estado'] = 'Libre'
                alumnos_atendidos.append({
                    'id': equipo['alumno']['id'],
                    'espera': equipo['alumno']['inicio_atencion'] - equipo['alumno']['llegada'],
                    'tiempo_total': tiempo_actual - equipo['alumno']['llegada']
                })
                equipo['alumno'] = None

            if equipo['estado'] == 'Libre' and cola:
                # Asignar nuevo alumno al equipo
                alumno = cola.pop(0)
                equipo['estado'] = 'Ocupado'
                equipo['fin_atencion'] = tiempo_actual + random.uniform(inf_inscripcion, sup_inscripcion)
                alumno['inicio_atencion'] = tiempo_actual
                equipo['alumno'] = alumno

        # Registrar estado en la tabla
        tabla_simulacion.append({
            'reloj': round(tiempo_actual, 2),
            'evento': f"Llegada Alumno {alumno_id}",
            'cola': len(cola),
            'equipos': [equipo['estado'] for equipo in equipos_estado],
            'alumnos': [f"Atendiendo Alumno {equipo['alumno']['id']}" if equipo['estado'] == 'Ocupado' else "Libre"
                        for equipo in equipos_estado]
        })

        alumno_id += 1

    # Calcular métricas finales
    tiempo_promedio_espera = sum([alumno['espera'] for alumno in alumnos_atendidos]) / len(alumnos_atendidos) if alumnos_atendidos else 0
    porcentaje_se_fueron = (alumnos_se_fueron / alumno_id) * 100

    return tabla_simulacion, tiempo_promedio_espera, porcentaje_se_fueron
