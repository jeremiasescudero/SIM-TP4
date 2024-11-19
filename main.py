import os
from flask import Flask, request, render_template, flash
from colas import simular

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates_new'))
app.secret_key = 'l0r3m1ps8md0l0rs1t4m3t'

@app.route('/', methods=['GET', 'POST'])
def main_menu():
    if request.method == 'POST':
        try:
            # Recibir y validar parámetros del formulario
            equipos = int(request.form.get('equipos', 0))
            inf_inscripcion = int(request.form.get('inf_inscripcion', 0))
            sup_inscripcion = int(request.form.get('sup_inscripcion', 0))
            media_llegada = float(request.form.get('media_llegada', 0.0))
            mant_min = int(request.form.get('mant_min', 0))
            mant_max = int(request.form.get('mant_max', 0))
            mant_intervalo = int(request.form.get('mant_intervalo', 0))
            mant_desviacion = float(request.form.get('mant_desviacion', 0.0))
            max_cola = int(request.form.get('max_cola', 0))
            tiempo_retorno = int(request.form.get('tiempo_retorno', 0))
            dias_simulacion = int(request.form.get('dias_simulacion', 0))

            # Validar valores básicos (puedes añadir más reglas si es necesario)
            if equipos <= 0 or dias_simulacion <= 0:
                flash("Los valores de 'equipos' y 'días de simulación' deben ser mayores a 0.", "error")
                return render_template('menu.html')

            # Llamar a la simulación con los parámetros
            tabla_simulacion, max_alumnos, num_equipos = simular(
                media_llegada=media_llegada,
                t_ins_min=inf_inscripcion,
                t_ins_max=sup_inscripcion,
                t_mant_min=mant_min,
                t_mant_max=mant_max,
                mant_intervalo=mant_intervalo,
                dias_simulacion=dias_simulacion,
                equipos=equipos,
                inf_inscripcion=inf_inscripcion,
                sup_inscripcion=sup_inscripcion,
                mant_desviacion=mant_desviacion,
                max_cola=max_cola,
                tiempo_retorno=tiempo_retorno
            )

            # Renderizar la tabla resultante
            return render_template(
                'nuevo_colas.html',
                tabla=tabla_simulacion,
                max_alumnos=int(max_alumnos),
                num_equipos=num_equipos,
                enumerate=enumerate
            )

        except ValueError as e:
            flash(f"Error en los datos ingresados: {e}", "error")
        except Exception as e:
            flash(f"Ocurrió un error durante la simulación: {e}", "error")

    # Renderizar el formulario inicial
    return render_template(
        'menu.html',
        equipos=6,
        inf_inscripcion=5,
        sup_inscripcion=8,
        media_llegada=2.0,
        t_mant_min=3,
        t_mant_max=10,
        mant_intervalo=60,
        mant_desviacion=3.0,
        max_cola=5,
        tiempo_retorno=30,
        dias_simulacion=1
    )

if __name__ == '__main__':
    app.run(debug=True, port=5003)
