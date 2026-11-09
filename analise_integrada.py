import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def simular_consumo_energetico():
    print("=== 1. SIMULAÇÃO COMPUTACIONAL DE CONSUMO E BATERIA (AURORA SIGER) ===")
    
    # Definindo o tempo (ciclos operacionais em horas - 24 horas em Marte / Sol)
    tempo = np.linspace(0, 24, 100)
    
    # Geração solar simulada (senoide modulada para o dia marciano)
    geracao_solar = np.maximum(0, 50 * np.sin(np.pi * tempo / 12))
    
    # Consumo base dos módulos da colônia (habitação, agricultura, suporte médico)
    consumo_base = 30 + 5 * np.sin(np.pi * tempo / 6)
    
    # Balanço energético (Geração - Consumo)
    balanco = geracao_solar - consumo_base
    
    # Estado de Carga da Bateria (SoC - State of Charge) integrando o balanco ao longo do tempo (método numérico simples)
    capacidade_bateria_inicial = 100.0
    soc = [capacidade_bateria_inicial]
    
    dt = tempo[1] - tempo[0]
    for b in balanco[1:]:
        novo_soc = soc[-1] + (b * dt * 0.1)  # fator de escala de carga
        novo_soc = np.clip(novo_soc, 10.0, 100.0) # limites operacionais de segurança da bateria
        soc.append(novo_soc)
        
    print(f"Simulação concluída para {len(tempo)} pontos temporais.")
    print(f"Estado final da bateria: {soc[-1]:.2f}%")
    
    # Integração Numérica (Área sob a curva de consumo para calcular energia total gasta)
    energia_total_gasta = np.trapezoid(consumo_base, tempo)
    print(f"Energia total consumida acumulada no ciclo: {energia_total_gasta:.2f} kWh")
    
    return tempo, geracao_solar, consumo_base, soc

def modelo_linear_previsao():
    print("\n=== 2. MODELAGEM LINEAR SIMPLES PARA APOIO À DECISÃO ===")
    
    # Dados simulados da colônia: [Ocupação do Módulo (pessoas), Temperatura Externa (ºC), Consumo Energético (kWh)]
    np.random.seed(42)
    n_registros = 50
    
    ocupacao = np.random.randint(5, 35, size=n_registros)
    temp_externa = np.random.uniform(-65, -10, size=n_registros)
    
    # Equação geradora com ruído: Consumo = 2.5 * ocupacao - 0.8 * temp_externa + ruidoso
    consumo_energetico = 2.5 * ocupacao - 0.8 * temp_externa + np.random.normal(0, 3, size=n_registros)
    
    df = pd.DataFrame({
        'Ocupacao': ocupacao,
        'TempExterna': temp_externa,
        'ConsumoKWh': consumo_energetico
    })
    
    print("Amostra dos dados coletados dos módulos:")
    print(df.head())
    
    # Regressão Linear Múltipla / Simples via matrizes (Solução dos Mínimos Quadrados Ordinários - OLS)
    # y = X * beta
    X = np.column_stack((np.ones(n_registros), df['Ocupacao'], df['TempExterna']))
    y = df['ConsumoKWh'].values
    
    # Beta = (X^T * X)^(-1) * X^T * y
    beta = np.linalg.inv(X.T @ X) @ X.T @ y
    
    print("\nCoeficientes do Modelo Linear Calculados:")
    print(f"Intercepto (Consumo Base Fixo): {beta[0]:.4f}")
    print(f"Coeficiente Ocupação (Impacto por pessoa): {beta[1]:.4f}")
    print(f"Coeficiente Temperatura Externa (Impacto térmico): {beta[2]:.4f}")
    
    # Avaliação simples do modelo (R² - Coeficiente de Determinação)
    y_pred = X @ beta
    ss_total = np.sum((y - np.mean(y))**2)
    ss_residual = np.sum((y - y_pred)**2)
    r_squared = 1 - (ss_residual / ss_total)
    
    print(f"Avaliação do Modelo (R²): {r_squared:.4f}")
    
    # Previsão de exemplo para nova situação crítica na colônia
    nova_ocupacao = 25
    nova_temp = -45.0
    consumo_previsto = beta[0] + beta[1] * nova_ocupacao + beta[2] * nova_temp
    print(f"\nPrevisão de Consumo para Ocupação={nova_ocupacao} pessoas e Temp={nova_temp}ºC: {consumo_previsto:.2f} kWh")

if __name__ == "__main__":
    simular_consumo_energetico()
    modelo_linear_previsao()