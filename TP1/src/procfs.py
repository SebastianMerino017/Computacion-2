import os


# devuelve una lista de todos los PIDs activos en el sistema
def listar_pids():
    pids = []
    for nombre in os.listdir('/proc'):
        if nombre.isdigit():
            pids.append(int(nombre))
    return pids


# lee y parsea /proc/<pid>/stat. Devuelve un dict con pid, nombre y estado
def leer_stat(pid):
    with open(f'/proc/{pid}/stat', 'r') as f:
        contenido = f.read()

    inicio_nombre = contenido.index('(')
    fin_nombre = contenido.rindex(')')

    nombre = contenido[inicio_nombre + 1 : fin_nombre]

    antes = contenido[:inicio_nombre].split()
    despues = contenido[fin_nombre + 1 :].split()

    return {
        'pid': int(antes[0]),
        'nombre': nombre,
        'estado': despues[0]
    }


# lee /proc/<pid>/status y devuelve un dict con los campos clave: valor
def leer_status(pid):
    datos = {}
    with open(f'/proc/{pid}/status', 'r') as f:
        for linea in f:
            clave, _, valor = linea.partition(':')
            datos[clave.strip()] = valor.strip()
    return datos