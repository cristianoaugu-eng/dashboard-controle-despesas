import pandas as pd
import os


def carregar_dados(caminho_dados="dados"):

    arquivos = [
        arq for arq in os.listdir(caminho_dados)
        if arq.endswith(".xlsx")
    ]

    lista_df = []

    for arquivo in arquivos:
        caminho = os.path.join(caminho_dados, arquivo)
        df = pd.read_excel(caminho)
        lista_df.append(df)

    df = pd.concat(lista_df, ignore_index=True)

    return tratar_dados(df)


def converter_moeda(serie):

    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce").fillna(0)

    serie = (
        serie.astype(str)
        .str.replace("R$", "", regex=False)
        .str.strip()
    )

    # Caso brasileiro: 3.995,68
    mascara_virgula = serie.str.contains(",", na=False)

    serie.loc[mascara_virgula] = (
        serie.loc[mascara_virgula]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    return pd.to_numeric(serie, errors="coerce").fillna(0)


def tratar_dados(df):

    df.columns = df.columns.str.strip()

    df["Data Baixa"] = pd.to_datetime(df["Data Baixa"], errors="coerce")
    df["Vencimento"] = pd.to_datetime(df["Vencimento"], errors="coerce")

    colunas_valor = [
        "Valor",
        "Juros",
        "Multa",
        "Desconto",
        "Pago"
    ]

    for coluna in colunas_valor:
        df[coluna] = converter_moeda(df[coluna])

    df["Categoria"] = (
        df["Taxa"]
        .astype(str)
        .str.replace(r"^\d+\-", "", regex=True)
        .str.strip()
    )

    df["Ano_Pagamento"] = df["Data Baixa"].dt.year
    df["Mes_Pagamento"] = df["Data Baixa"].dt.month
    df["Mes_Ano"] = df["Data Baixa"].dt.strftime("%m/%Y")

    hoje = pd.Timestamp.today()

    df["Status"] = "Pago"

    df.loc[
        (df["Data Baixa"].isna()) &
        (df["Vencimento"] >= hoje),
        "Status"
    ] = "Em Aberto"

    df.loc[
        (df["Data Baixa"].isna()) &
        (df["Vencimento"] < hoje),
        "Status"
    ] = "Vencido"

    df = df.sort_values("Data Baixa")

    return df