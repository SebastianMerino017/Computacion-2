# tests/test_procfs.py - Tests básicos para las funciones de procfs.py

import sys
import os

# Agregamos src/ al path para poder importar los módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import procfs


def test_listar_pids_retorna_lista():
    pids = procfs.listar_pids()
    assert isinstance(pids, list), "listar_pids() debe retornar una lista"
    assert len(pids) > 0, "debe haber al menos un proceso corriendo"
    print("OK - listar_pids retorna lista no vacía")


def test_listar_pids_son_enteros():
    pids = procfs.listar_pids()
    for pid in pids:
        assert isinstance(pid, int), f"cada PID debe ser int, got {type(pid)}"
    print("OK - todos los PIDs son enteros")


def test_leer_stat_pid1():
    stat = procfs.leer_stat(1)
    assert 'pid' in stat, "stat debe tener campo 'pid'"
    assert 'nombre' in stat, "stat debe tener campo 'nombre'"
    assert 'estado' in stat, "stat debe tener campo 'estado'"
    assert stat['pid'] == 1, "el PID leído debe ser 1"
    assert stat['estado'] in ('R', 'S', 'D', 'T', 'Z'), f"estado inválido: {stat['estado']}"
    print(f"OK - leer_stat(1): nombre={stat['nombre']} estado={stat['estado']}")


def test_leer_status_pid1():
    status = procfs.leer_status(1)
    assert isinstance(status, dict), "leer_status() debe retornar un dict"
    assert 'Name' in status, "status debe tener campo 'Name'"
    assert 'Pid' in status, "status debe tener campo 'Pid'"
    assert 'PPid' in status, "status debe tener campo 'PPid'"
    print(f"OK - leer_status(1): Name={status['Name']} PPid={status['PPid']}")


def test_pid_invalido_lanza_excepcion():
    try:
        procfs.leer_stat(999999)
        assert False, "debería haber lanzado FileNotFoundError"
    except FileNotFoundError:
        print("OK - PID inválido lanza FileNotFoundError")


if __name__ == '__main__':
    print("Corriendo tests de procfs...\n")
    test_listar_pids_retorna_lista()
    test_listar_pids_son_enteros()
    test_leer_stat_pid1()
    test_leer_status_pid1()
    test_pid_invalido_lanza_excepcion()
    print("\nTodos los tests pasaron!")