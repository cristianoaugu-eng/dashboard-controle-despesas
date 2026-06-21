import pandas as pd
import os


def carregar_dados(caminho_dados="dados"):

    arquivo_base = "despesas_historico.xlsx"
    caminho_base = os.path.join(caminho_dados, arquivo_base)

    if not os.path.exists(caminho_base):
        raise FileNotFoundError(
            "Arquivo base 'despesas_historico.xlsx' não encontrado na pasta dados."
        )

    arquivos = [
        arq for arq in os.listdir(caminho_dados)
        if arq.endswith(".xlsx")
        and not arq.startswith("~$")
        and arq != "despesas_historico_real.xlsx"
    ]

    if arquivo_base not in arquivos:
        raise FileNotFoundError(
            "O arquivo despesas_historico.xlsx precisa estar dentro da pasta dados."
        )

    # Lê arquivo base
    df_base = pd.read_excel(caminho_base)
    df_base.columns = df_base.columns.str.strip()

    colunas_base = list(df_base.columns)

    lista_df = []

    # Lê todos os arquivos da pasta dados
    for arquivo in arquivos:

        caminho = os.path.join(caminho_dados, arquivo)

        df_temp = pd.read_excel(caminho)
        df_temp.columns = df_temp.columns.str.strip()

        colunas_arquivo = list(df_temp.columns)

        colunas_faltando = [
            col for col in colunas_base
            if col not in colunas_arquivo
        ]

        colunas_extras = [
            col for col in colunas_arquivo
            if col not in colunas_base
        ]

        if colunas_faltando or colunas_extras:
            raise ValueError(
                f"""
                Erro no arquivo: {arquivo}

                As colunas não estão iguais ao arquivo base despesas_historico.xlsx.

                Colunas faltando:
                {colunas_faltando}

                Colunas extras:
                {colunas_extras}
                """
            )

        # Reordena as colunas para garantir padronização
        df_temp = df_temp[colunas_base]

        # Identifica origem do arquivo
        df_temp["Arquivo_Origem"] = arquivo

        lista_df.append(df_temp)

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

    mascara_virgula = serie.str.contains(",", na=False)

    serie.loc[mascara_virgula] = (
        serie.loc[mascara_virgula]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    return pd.to_numeric(serie, errors="coerce").fillna(0)


def tratar_dados(df):

    df.columns = df.columns.str.strip()

    if "Filial" not in df.columns:
        df.insert(0, "Filial", "Matriz")

    df["Data Baixa"] = pd.to_datetime(
        df["Data Baixa"],
        errors="coerce"
    )

    df["Vencimento"] = pd.to_datetime(
        df["Vencimento"],
        errors="coerce"
    )

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