# Gerador de Dados Iniciais Simulados - Aurora Siger
# Cria o arquivo dados_aurora_siger.csv com:
# - 5 módulos da colônia;
# - 10 sensores simulados;
# - 32 ciclos de uma hora;
# - 320 leituras reproduzíveis.

import csv
import math

from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import CAMINHO_CSV

# Definindo os módulos da colônia
# Formato: codigo -> (nome, tipo, critico)
MODULOS = {
    "MOD-HAB-01": ("Habitação", "habitacao", 1),
    "MOD-ENE-01": ("Energia", "energia", 1),
    "MOD-AGR-01": ("Agricultura", "agricultura", 0),
    "MOD-LAB-01": ("Laboratório", "laboratorio", 0),
    "MOD-COM-01": ("Comunicação", "comunicacao", 1),
}

# Definindo os sensores de cada módulo
# Formato: (modulo_codigo, sensor_codigo, tipo, unidade)
SENSORES = [
    ("MOD-HAB-01", "SEN-HAB-CONS-01", "consumo_kw", "kW"),
    ("MOD-HAB-01", "SEN-HAB-TEMP-01", "temperatura", "°C"),

    ("MOD-ENE-01", "SEN-ENE-GER-01", "geracao_kw", "kW"),
    ("MOD-ENE-01", "SEN-ENE-LUX-01", "luminosidade", "lux"),

    ("MOD-AGR-01", "SEN-AGR-CONS-01", "consumo_kw", "kW"),
    ("MOD-AGR-01", "SEN-AGR-UMI-01", "umidade", "%"),

    ("MOD-LAB-01", "SEN-LAB-CONS-01", "consumo_kw", "kW"),
    ("MOD-LAB-01", "SEN-LAB-TEMP-01", "temperatura", "°C"),

    ("MOD-COM-01", "SEN-COM-CONS-01", "consumo_kw", "kW"),
    ("MOD-COM-01", "SEN-COM-LAT-01", "latencia_ms", "ms"),
]

# Definindo as colunas do CSV
CAMPOS_CSV = [
    "modulo_codigo",
    "modulo_nome",
    "modulo_tipo",
    "modulo_critico",
    "sensor_codigo",
    "sensor_tipo",
    "sensor_unidade",
    "ciclo",
    "instante",
    "valor",
]

# Retorna um dicionário com as medições de um ciclo
def calcular_valores_simulados(ciclo):
    hora = (ciclo - 1) % 24

    # Curva solar ilustrativa: zero durante a noite e maior geração por volta do meio-dia.
    fator_solar = max(
        0.0,
        math.sin(math.pi * (hora - 6) / 12)
    )

    valores = {
        "SEN-HAB-CONS-01": 2.2 + 0.2 * (ciclo % 5),
        "SEN-HAB-TEMP-01": 21 + 1.8 * math.sin(ciclo / 4),

        "SEN-ENE-GER-01": 8.5 * fator_solar,
        "SEN-ENE-LUX-01": 750 * fator_solar,

        "SEN-AGR-CONS-01": 0.8 + 0.12 * (ciclo % 4),
        "SEN-AGR-UMI-01": 55 + 6 * math.sin(ciclo / 5),

        "SEN-LAB-CONS-01": 1.1 + 0.18 * (ciclo % 4),
        "SEN-LAB-TEMP-01": 20 + 1.2 * math.sin(ciclo / 6),

        "SEN-COM-CONS-01": 0.35 + 0.05 * (ciclo % 3),
        "SEN-COM-LAT-01": 210 + 8 * (ciclo % 5),
    }

    return valores


def gerar_csv_inicial(caminho_csv=CAMINHO_CSV):
    """
    Gera as leituras simuladas no CSV.

    Retorna a quantidade de linhas de dados gravadas.
    """

    caminho_csv = Path(caminho_csv)

    instante_inicial = datetime(
        2026, 11, 9, 0, 0, 0,
        tzinfo=timezone.utc
    )

    quantidade = 0

    with caminho_csv.open(
        mode="w",
        newline="",
        encoding="utf-8"
    ) as arquivo:

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=CAMPOS_CSV
        )

        escritor.writeheader()

        # Cada ciclo representa uma hora simulada.
        for ciclo in range(1, 33):

            instante = (
                instante_inicial
                + timedelta(hours=ciclo - 1)
            )

            valores = calcular_valores_simulados(ciclo)

            # Registra uma leitura de cada sensor no ciclo.
            for (
                modulo_codigo,
                sensor_codigo,
                sensor_tipo,
                sensor_unidade
            ) in SENSORES:

                nome, tipo, critico = MODULOS[modulo_codigo]

                escritor.writerow({
                    "modulo_codigo": modulo_codigo,
                    "modulo_nome": nome,
                    "modulo_tipo": tipo,
                    "modulo_critico": critico,
                    "sensor_codigo": sensor_codigo,
                    "sensor_tipo": sensor_tipo,
                    "sensor_unidade": sensor_unidade,
                    "ciclo": ciclo,
                    "instante": instante.isoformat().replace(
                        "+00:00", "Z"
                    ),
                    "valor": round(valores[sensor_codigo], 2),
                })

                quantidade += 1

    return quantidade


if __name__ == "__main__":
    total = gerar_csv_inicial()

    print(f"Arquivo gerado: {CAMINHO_CSV.name}")
    print(f"Total de leituras: {total}")