import os
from flask import Flask, request, render_template
from colas import simular

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates_new'))
app.secret_key = 'l0r3m1ps8md0l0rs1t4m3t'


@app.route('/', methods=['GET', 'POST'])
def main_menu():
    if request.method == 'POST':
        
        equipos = int(request.form['equipos'])
        inf_inscripcion = int(request.form['inf_inscripcion'])
        sup_inscripcion = int(request.form['sup_inscripcion'])
        media_llegada = float(request.form['media_llegada'])
        mant_min = int(request.form['mant_min'])
        mant_max = int(request.form['mant_max'])
        mant_intervalo = int(request.form['mant_intervalo'])
        mant_desviacion = float(request.form['mant_desviacion'])
        max_cola = int(request.form['max_cola'])
        tiempo_retorno = int(request.form['tiempo_retorno'])

        
        tabla_simulacion, max_alumnos, num_equipos = simular(
            equipos=equipos,
            inf_inscripcion=inf_inscripcion,
            sup_inscripcion=sup_inscripcion,
            media_llegada=media_llegada,
            mant_min=mant_min,
            mant_max=mant_max,
            mant_intervalo=mant_intervalo,
            mant_desviacion=mant_desviacion,
            max_cola=max_cola,
            tiempo_retorno=tiempo_retorno
        )

        
        num_equipos = int(num_equipos)

        return render_template(
            'nuevo_colas.html',
            tabla=tabla_simulacion,
            max_alumnos=max_alumnos,
            num_equipos=num_equipos,
            enumerate=enumerate
        )

    
    return render_template(
        'menu.html',
        equipos=6,
        inf_inscripcion=5,
        sup_inscripcion=8,
        media_llegada=2.0,
        mant_min=3,
        mant_max=10,
        mant_intervalo=60,
        mant_desviacion=3.0,
        max_cola=5,
        tiempo_retorno=30
    )


if __name__ == '__main__':
    app.run(debug=True, port=5003)
