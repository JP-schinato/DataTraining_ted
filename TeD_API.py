import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time

# Cidades para análise
cidades = {
    'São Paulo': {'lat': -23.5505, 'lon': -46.6333},
    'Nova York': {'lat': 40.7128, 'lon': -74.0060}, 
    'Londres': {'lat': 51.5074, 'lon': -0.1278}
}

def pegar_dados_cidade(nome, coords):
    print(f"Coletando dados de {nome}...")
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        'latitude': coords['lat'],
        'longitude': coords['lon'],
        'start_date': '2014-01-01',
        'end_date': '2023-12-31',
        'daily': 'temperature_2m_mean',
        'timezone': 'UTC'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame({
            'data': pd.to_datetime(data['daily']['time']),
            'temperatura': data['daily']['temperature_2m_mean'],
            'cidade': nome
        })
        
        print(f"Coletados {len(df)} registros de {nome}")
        return df
        
    except Exception as e:
        print(f"Erro ao coletar dados de {nome}: {e}")
        return pd.DataFrame()

# Coletar dados
dados_completos = []

for nome, coords in cidades.items():
    df_cidade = pegar_dados_cidade(nome, coords)
    if not df_cidade.empty:
        dados_completos.append(df_cidade)
    time.sleep(0.5)  # Pausa para evitar sobrecarga da API

if not dados_completos:
    print("Nenhum dado foi coletado. Encerrando.")
    exit()

# Combinar todos os dados
df = pd.concat(dados_completos, ignore_index=True)
df = df.dropna()

print(f"Total de registros: {len(df)}")

# Preparar dados para análise
df['ano'] = df['data'].dt.year
df_anual = df.groupby(['cidade', 'ano'])['temperatura'].mean().reset_index()

# Análise temporal
df_global = df.groupby('ano')['temperatura'].mean()

# Gráficos
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Gráfico 1: Temperatura por cidade
colors = plt.cm.tab10(np.linspace(0, 1, len(cidades)))
for i, cidade in enumerate(cidades.keys()):
    dados_cidade = df_anual[df_anual['cidade'] == cidade]
    axes[0,0].plot(dados_cidade['ano'], dados_cidade['temperatura'], 
                   marker='o', label=cidade, color=colors[i])

axes[0,0].set_title('Temperatura por Cidade')
axes[0,0].set_xlabel('Ano')
axes[0,0].set_ylabel('Temperatura (°C)')
axes[0,0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
axes[0,0].grid(True)

# Gráfico 2: Tendência global
axes[0,1].plot(df_global.index, df_global.values, 'o-', linewidth=2)

# Linha de tendência
z = np.polyfit(df_global.index, df_global.values, 1)
p = np.poly1d(z)
axes[0,1].plot(df_global.index, p(df_global.index), '--', linewidth=2)

axes[0,1].set_title('Tendência Global')
axes[0,1].set_xlabel('Ano')
axes[0,1].set_ylabel('Temperatura Média (°C)')
axes[0,1].grid(True)

# Gráfico 3: Comparação por períodos
periodo1 = df[df['ano'] <= 2018]['temperatura'].mean()
periodo2 = df[df['ano'] > 2018]['temperatura'].mean()

axes[1,0].bar(['2014-2018', '2019-2023'], [periodo1, periodo2])
axes[1,0].set_title('Comparação de Períodos')
axes[1,0].set_ylabel('Temperatura Média (°C)')

# Gráfico 4: Temperatura média por cidade
temp_por_cidade = df.groupby('cidade')['temperatura'].mean().sort_values(ascending=False)
axes[1,1].barh(range(len(temp_por_cidade)), temp_por_cidade.values)
axes[1,1].set_yticks(range(len(temp_por_cidade)))
axes[1,1].set_yticklabels(temp_por_cidade.index)
axes[1,1].set_xlabel('Temperatura Média (°C)')
axes[1,1].set_title('Ranking de Temperatura por Cidade')

plt.tight_layout()
plt.show()

# Estatísticas
print("\n--- RESULTADOS ---")
print(f"Temperatura média 2014-2018: {periodo1:.2f}°C")
print(f"Temperatura média 2019-2023: {periodo2:.2f}°C")
print(f"Diferença: {periodo2 - periodo1:+.2f}°C")

taxa_anual = z[0]
print(f"Taxa de mudança: {taxa_anual:+.3f}°C por ano")

if taxa_anual > 0:
    print("Tendência: AQUECIMENTO")
else:
    print("Tendência: ESFRIAMENTO")

# Estatísticas por cidade
print("\nPor cidade:")
for cidade in cidades.keys():
    temp_media = df[df['cidade'] == cidade]['temperatura'].mean()
    print(f"{cidade}: {temp_media:.1f}°C")
