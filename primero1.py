from fmpy import *
from fmpy.util import plot_result
import numpy as np
import shutil
import os
import matplotlib.pyplot as plt

# Ruta al archivo FMU exportado desde MATLAB
fmu_filename = 'battery_convertidor_ac_dc_4.fmu'

# Extraer el FMU
unzipdir = extract(fmu_filename)

# Leer la descripción del modelo
model_description = read_model_description(unzipdir)

# Crear instancia del FMU para CoSimulation
fmu_instance = instantiate_fmu(unzipdir, model_description, fmi_type='CoSimulation')

# Configuración de simulación
start_time = 0.0
stop_time = 3.0
#step_size = 0.001
step_size = 1e-5
# Inicializar simulación
fmu_instance.setupExperiment(startTime=start_time)
fmu_instance.enterInitializationMode()

# Entradas constantes
input_values = {
    'Pref_Bat': 50e3,
    'Pref_Ultr': 20e3,
    'Pref_smes': 20e3,
    'Pref_ac_dc': 40e3
}

# Asignar valores de entrada
for name, value in input_values.items():
    vr = [v for v in model_description.modelVariables if v.name == name][0].valueReference
    fmu_instance.setReal([vr], [value])

fmu_instance.exitInitializationMode()

# Variables de salida a registrar
output_names = ['V_LOAD_AC', 'I_LOAD_AC', 'P_LOAD_AC','V_LOAD_DC','I_LOAD_DC','P_LOAD_DC','P_GRID','V_INVERSOR','I_INVERSOR','P_INVERSOR','BAT_SOC',
                'V_SMES','I_SMES','P_SMES','V_UC','I_UC','P_UC','SOC_UC']
output_vrs = [
    [v for v in model_description.modelVariables if v.name == name][0].valueReference
    for name in output_names
]

# Simulación paso a paso
time = start_time
times = []
outputs = {name: [] for name in output_names}

while time < stop_time:
    fmu_instance.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)
    values = fmu_instance.getReal(output_vrs)
    times.append(time)
    for name, value in zip(output_names, values):
        outputs[name].append(value)
    time += step_size

# Finalizar simulación
fmu_instance.terminate()
fmu_instance.freeInstance()
shutil.rmtree(unzipdir)
# Mostrar vectores de resultados en consola con formato tabular claro
max_name_length = max(len(name) for name in output_names)

for name in output_names:
    print(f"\n=== Datos para {name} ===")
    header_time = 'Tiempo [s]'
    header_value = name
    print(f"{header_time:>12} | {header_value:>{max_name_length}}")
    print("-" * (15 + max_name_length))

    for t, val in zip(times, outputs[name]):
        print(f"{t:12.4f} | {val:>{max_name_length}.4f}")

# Graficar cada variable de salida por separado
for name in output_names:
    plt.figure(figsize=(8, 4))
    plt.plot(times, outputs[name], label=name, color='tab:blue')
    plt.title(f'Salida: {name}')
    plt.xlabel('Tiempo [s]')
    plt.ylabel(name)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

