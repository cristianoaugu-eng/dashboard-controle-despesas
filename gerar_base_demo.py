import pandas as pd
import numpy as np
import os

ARQUIVO_ORIGEM = "dados/despesas_historico.xlsx"
ARQUIVO_SAIDA = "dados/despesas_demo.xlsx"

df = pd.read_excel(ARQUIVO_ORIGEM)

df.columns = df.columns.str.strip()

# Criar fornecedores fictícios
nomes_unicos = df["Nome"].dropna().unique()

mapa_fornecedores = {
    nome: f"Fornecedor {i+1:03d}"
    for i, nome in enumerate(nomes_unicos)
}

df["Nome"] = df["Nome"].map(mapa_fornecedores)

# Criar matrículas fictícias
matriculas_unicas = df["Matrícula"].dropna().unique()

mapa_matriculas = {
    matricula: f"{i+1:05d}"
    for i, matricula in enumerate(matriculas_unicas)
}

df["Matrícula"] = df["Matrícula"].map(mapa_matriculas)

# Alterar valores mantendo aparência realista
colunas_valor = ["Valor", "Juros", "Multa", "Desconto", "Pago"]

for coluna in colunas_valor:
    if coluna in df.columns:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)

        fator = np.random.uniform(
            0.70,
            1.30,
            size=len(df)
        )

        df[coluna] = (df[coluna] * fator).round(2)

# Padronizar filial demo
if "Filial" not in df.columns:
    df.insert(0, "Filial", "Matriz Demo")
else:
    df["Filial"] = "Matriz Demo"

# Garantir pasta de saída
os.makedirs("dados", exist_ok=True)

df.to_excel(
    ARQUIVO_SAIDA,
    index=False
)

print("Base demo criada com sucesso!")
print(f"Arquivo gerado: {ARQUIVO_SAIDA}")
print(f"Linhas: {len(df)}")