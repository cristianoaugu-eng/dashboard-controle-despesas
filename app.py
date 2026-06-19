import streamlit as st
import pandas as pd
import plotly.express as px

from utils.tratamento import carregar_dados

st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="📊",
    layout="wide"
)


def formatar_valor(valor):
    if pd.isna(valor):
        valor = 0

    if valor >= 1_000_000:
        texto = f"R$ {valor / 1_000_000:.2f} Mi"
    elif valor >= 1_000:
        texto = f"R$ {valor / 1_000:.1f} mil"
    else:
        texto = f"R$ {valor:.2f}"

    return texto.replace(".", ",")


df = carregar_dados()

if "Filial" not in df.columns:
    df["Filial"] = "Matriz"

# =====================================================
# FILTROS
# =====================================================

st.sidebar.header("🔎 Filtros")

filiais = sorted(df["Filial"].dropna().unique())

filial_sel = st.sidebar.multiselect(
    "Filial",
    filiais,
    default=filiais
)

competencias = (
    df[["Data Baixa", "Mes_Ano"]]
    .dropna()
    .drop_duplicates()
    .sort_values("Data Baixa")["Mes_Ano"]
    .unique()
)

competencia_sel = st.sidebar.multiselect(
    "Competência",
    competencias,
    default=competencias
)

categorias = sorted(df["Categoria"].dropna().unique())

categoria_sel = st.sidebar.multiselect(
    "Categoria",
    categorias,
    default=categorias
)

fornecedores = sorted(df["Nome"].dropna().unique())

fornecedor_sel = st.sidebar.multiselect(
    "Fornecedor",
    fornecedores
)

# =====================================================
# APLICAR FILTROS
# =====================================================

df_filtrado = df.copy()

df_filtrado = df_filtrado[df_filtrado["Filial"].isin(filial_sel)]
df_filtrado = df_filtrado[df_filtrado["Mes_Ano"].isin(competencia_sel)]
df_filtrado = df_filtrado[df_filtrado["Categoria"].isin(categoria_sel)]

if fornecedor_sel:
    df_filtrado = df_filtrado[df_filtrado["Nome"].isin(fornecedor_sel)]

# =====================================================
# SIDEBAR - RESUMO
# =====================================================

st.sidebar.markdown("---")

st.sidebar.metric(
    "📄 Registros",
    f"{len(df_filtrado):,}".replace(",", ".")
)

st.sidebar.metric(
    "🏢 Fornecedores",
    df_filtrado["Nome"].nunique()
)

st.sidebar.metric(
    "🏷️ Categorias",
    df_filtrado["Categoria"].nunique()
)

# =====================================================
# TÍTULO E ABAS
# =====================================================

st.title("📊 Dashboard Financeiro de Despesas")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Resumo",
    "🏷️ Categorias",
    "🏢 Fornecedores",
    "📈 Evolução",
    "🔮 Forecast"
])

# =====================================================
# ABA 1 - RESUMO
# =====================================================

with tab1:

    total_pago = df_filtrado["Pago"].sum()
    qtd_lancamentos = len(df_filtrado)
    ticket_medio = df_filtrado["Pago"].mean()
    maior_despesa = df_filtrado["Pago"].max()
    qtd_categorias = df_filtrado["Categoria"].nunique()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("💰 Total Pago", formatar_valor(total_pago))
    col2.metric("📄 Lançamentos", f"{qtd_lancamentos:,}".replace(",", "."))
    col3.metric("📊 Ticket Médio", formatar_valor(ticket_medio))
    col4.metric("🔺 Maior Despesa", formatar_valor(maior_despesa))
    col5.metric("🏷️ Categorias", qtd_categorias)

    st.divider()

    st.subheader("📈 Evolução Mensal das Despesas")

    evolucao = (
        df_filtrado
        .groupby("Mes_Ano", as_index=False)["Pago"]
        .sum()
    )

    evolucao["Data_Ordenacao"] = pd.to_datetime(
        evolucao["Mes_Ano"],
        format="%m/%Y"
    )

    evolucao = evolucao.sort_values("Data_Ordenacao")

    fig = px.line(
        evolucao,
        x="Mes_Ano",
        y="Pago",
        markers=True
    )

    fig.update_layout(
        xaxis_title="Competência",
        yaxis_title="Valor Pago (R$)",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Visualizar Base de Dados"):
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True
        )

# =====================================================
# ABA 2 - CATEGORIAS
# =====================================================

with tab2:

    st.subheader("🏷️ Análise por Categoria")

    categorias_df = (
        df_filtrado
        .groupby("Categoria", as_index=False)["Pago"]
        .sum()
        .sort_values("Pago", ascending=False)
    )

    total_categorias = categorias_df["Pago"].sum()

    categorias_df["% Total"] = (
        categorias_df["Pago"] / total_categorias * 100
        if total_categorias > 0
        else 0
    )

    top_categorias = categorias_df.head(15)

    fig_cat = px.bar(
        top_categorias.sort_values("Pago", ascending=True),
        x="Pago",
        y="Categoria",
        orientation="h",
        text="Pago",
        title="Top 15 Categorias por Valor Pago"
    )

    fig_cat.update_traces(
        texttemplate="%{x:,.0f}",
        textposition="outside"
    )

    fig_cat.update_layout(
        xaxis_title="Valor Pago (R$)",
        yaxis_title="Categoria",
        height=650
    )

    st.plotly_chart(fig_cat, use_container_width=True)

    st.divider()

    tabela_cat = categorias_df.copy()
    tabela_cat["Valor Pago"] = tabela_cat["Pago"].apply(formatar_valor)
    tabela_cat["% Total"] = tabela_cat["% Total"].map(
        lambda x: f"{x:.2f}%".replace(".", ",")
    )

    tabela_cat = tabela_cat[["Categoria", "Valor Pago", "% Total"]]

    st.subheader("📋 Tabela de Categorias")

    st.dataframe(
        tabela_cat,
        use_container_width=True,
        hide_index=True
    )

# =====================================================
# ABA 3 - FORNECEDORES
# =====================================================

with tab3:

    st.subheader("🏢 Análise por Fornecedor")

    fornecedores_df = (
        df_filtrado
        .groupby("Nome", as_index=False)["Pago"]
        .sum()
        .sort_values("Pago", ascending=False)
    )

    total_fornecedores = fornecedores_df["Pago"].sum()

    fornecedores_df["% Total"] = (
        fornecedores_df["Pago"] / total_fornecedores * 100
        if total_fornecedores > 0
        else 0
    )

    top_fornecedores = fornecedores_df.head(20)

    fig_forn = px.bar(
        top_fornecedores.sort_values("Pago", ascending=True),
        x="Pago",
        y="Nome",
        orientation="h",
        text="Pago",
        title="Top 20 Fornecedores por Valor Pago"
    )

    fig_forn.update_traces(
        texttemplate="%{x:,.0f}",
        textposition="outside"
    )

    fig_forn.update_layout(
        xaxis_title="Valor Pago (R$)",
        yaxis_title="Fornecedor",
        height=750
    )

    st.plotly_chart(fig_forn, use_container_width=True)

    st.divider()

    tabela_forn = fornecedores_df.copy()
    tabela_forn["Valor Pago"] = tabela_forn["Pago"].apply(formatar_valor)
    tabela_forn["% Total"] = tabela_forn["% Total"].map(
        lambda x: f"{x:.2f}%".replace(".", ",")
    )

    tabela_forn = tabela_forn[["Nome", "Valor Pago", "% Total"]]
    tabela_forn = tabela_forn.rename(columns={"Nome": "Fornecedor"})

    st.subheader("📋 Tabela de Fornecedores")

    st.dataframe(
        tabela_forn,
        use_container_width=True,
        hide_index=True
    )

# =====================================================
# ABA 4 - EVOLUÇÃO
# =====================================================

with tab4:

    st.subheader("📈 Análise de Evolução das Despesas")

    evolucao_mes = (
        df_filtrado
        .groupby("Mes_Ano", as_index=False)
        .agg(
            Valor_Pago=("Pago", "sum"),
            Lancamentos=("Pago", "count")
        )
    )

    evolucao_mes["Data_Ordenacao"] = pd.to_datetime(
        evolucao_mes["Mes_Ano"],
        format="%m/%Y"
    )

    evolucao_mes = evolucao_mes.sort_values("Data_Ordenacao")

    # -----------------------------
    # Gráfico 1 - Valor pago
    # -----------------------------

    fig_evolucao_valor = px.bar(
        evolucao_mes,
        x="Mes_Ano",
        y="Valor_Pago",
        title="Valor Pago por Competência",
        text="Valor_Pago"
    )

    fig_evolucao_valor.update_traces(
        texttemplate="%{y:,.0f}",
        textposition="outside"
    )

    fig_evolucao_valor.update_layout(
        xaxis_title="Competência",
        yaxis_title="Valor Pago (R$)",
        height=500
    )

    st.plotly_chart(
        fig_evolucao_valor,
        use_container_width=True
    )

    # -----------------------------
    # Gráfico 2 - Lançamentos
    # -----------------------------

    fig_evolucao_qtd = px.line(
        evolucao_mes,
        x="Mes_Ano",
        y="Lancamentos",
        markers=True,
        title="Quantidade de Lançamentos por Competência"
    )

    fig_evolucao_qtd.update_layout(
        xaxis_title="Competência",
        yaxis_title="Quantidade de Lançamentos",
        height=500
    )

    st.plotly_chart(
        fig_evolucao_qtd,
        use_container_width=True
    )

    st.divider()

    # -----------------------------
    # Comparativo anual
    # -----------------------------

    st.subheader("📊 Comparativo Anual")

    comparativo_ano = (
        df_filtrado
        .groupby("Ano_Pagamento", as_index=False)["Pago"]
        .sum()
        .sort_values("Ano_Pagamento")
    )

    fig_comparativo_ano = px.bar(
        comparativo_ano,
        x="Ano_Pagamento",
        y="Pago",
        text="Pago",
        title="Total Pago por Ano"
    )

    fig_comparativo_ano.update_traces(
        texttemplate="%{y:,.0f}",
        textposition="outside"
    )

    fig_comparativo_ano.update_layout(
        xaxis_title="Ano",
        yaxis_title="Valor Pago (R$)",
        height=450
    )

    st.plotly_chart(
        fig_comparativo_ano,
        use_container_width=True
    )

    # -----------------------------
    # Tabela
    # -----------------------------

    tabela_evolucao = evolucao_mes.copy()

    tabela_evolucao["Valor Pago"] = tabela_evolucao["Valor_Pago"].apply(formatar_valor)

    tabela_evolucao = tabela_evolucao[
        [
            "Mes_Ano",
            "Valor Pago",
            "Lancamentos"
        ]
    ]

    tabela_evolucao = tabela_evolucao.rename(
        columns={
            "Mes_Ano": "Competência",
            "Lancamentos": "Lançamentos"
        }
    )

    st.subheader("📋 Tabela de Evolução")

    st.dataframe(
        tabela_evolucao,
        use_container_width=True,
        hide_index=True
    )

# =====================================================
# ABA 5 - FORECAST
# =====================================================

with tab5:

    st.subheader("🔮 Forecast de Despesas até Dezembro")

    df_forecast = df_filtrado.copy()

    meses_dict = {
        1: "Jan",
        2: "Fev",
        3: "Mar",
        4: "Abr",
        5: "Mai",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Set",
        10: "Out",
        11: "Nov",
        12: "Dez"
    }

    # -----------------------------
    # Base mensal por ano
    # -----------------------------

    base_mensal = (
        df_forecast
        .groupby(
            ["Ano_Pagamento", "Mes_Pagamento"],
            as_index=False
        )["Pago"]
        .sum()
    )

    comp_2025 = base_mensal[
        base_mensal["Ano_Pagamento"] == 2025
    ][["Mes_Pagamento", "Pago"]].rename(
        columns={"Pago": "Pago_2025"}
    )

    comp_2026 = base_mensal[
        base_mensal["Ano_Pagamento"] == 2026
    ][["Mes_Pagamento", "Pago"]].rename(
        columns={"Pago": "Pago_2026"}
    )

    comparativo_final = pd.merge(
        comp_2025,
        comp_2026,
        on="Mes_Pagamento",
        how="inner"
    )

    comparativo_final["Variacao_%"] = (
        (
            comparativo_final["Pago_2026"]
            /
            comparativo_final["Pago_2025"]
        ) - 1
    ) * 100

    crescimento_medio = comparativo_final["Variacao_%"].mean()

    if pd.isna(crescimento_medio):
        crescimento_medio = 0

    # -----------------------------
    # Realizado 2026
    # -----------------------------

    realizado_2026 = comp_2026.copy()

    if realizado_2026.empty:
        st.warning("Não há dados de 2026 para calcular o forecast.")
        st.stop()

    meses_realizados = sorted(realizado_2026["Mes_Pagamento"].unique())

    ultimo_mes_realizado = max(meses_realizados)

    total_realizado_2026 = realizado_2026["Pago_2026"].sum()

    media_mensal_2026 = realizado_2026["Pago_2026"].mean()

    # -----------------------------
    # Forecast baseado em 2025 + crescimento médio
    # -----------------------------

    meses_restantes = list(range(ultimo_mes_realizado + 1, 13))

    forecast_lista = []

    for mes in meses_restantes:

        valor_2025_mes = comp_2025.loc[
            comp_2025["Mes_Pagamento"] == mes,
            "Pago_2025"
        ]

        if not valor_2025_mes.empty:
            valor_base = valor_2025_mes.iloc[0]
        else:
            valor_base = media_mensal_2026

        valor_forecast = valor_base * (1 + crescimento_medio / 100)

        forecast_lista.append({
            "Mes_Pagamento": mes,
            "Valor": valor_forecast,
            "Tipo": "Forecast"
        })

    forecast_df = pd.DataFrame(forecast_lista)

    total_forecast = (
        forecast_df["Valor"].sum()
        if not forecast_df.empty
        else 0
    )

    total_previsto_2026 = total_realizado_2026 + total_forecast

    total_pago_2025 = comp_2025["Pago_2025"].sum()

    variacao_prevista_ano = (
        (
            total_previsto_2026 / total_pago_2025
        ) - 1
    ) * 100 if total_pago_2025 > 0 else 0

    # -----------------------------
    # KPIs
    # -----------------------------

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "💰 Pago em 2025",
        formatar_valor(total_pago_2025)
    )

    col2.metric(
        "✅ Realizado 2026",
        formatar_valor(total_realizado_2026)
    )

    col3.metric(
        "🔮 Forecast Jun-Dez",
        formatar_valor(total_forecast)
    )

    col4.metric(
        "📅 Previsto 2026",
        formatar_valor(total_previsto_2026)
    )

    col5.metric(
        "📈 Aumento Médio",
        f"{crescimento_medio:.1f}%".replace(".", ",")
    )

    st.metric(
        "📊 Variação Prevista 2026 x 2025",
        f"{variacao_prevista_ano:.1f}%".replace(".", ",")
    )

    st.divider()

    # -----------------------------
    # Gráfico comparativo 2025 x 2026
    # -----------------------------

    st.subheader("📊 Comparativo Mês a Mês - 2025 x 2026")

    grafico_comp = comparativo_final.copy()

    grafico_comp["Mes"] = grafico_comp["Mes_Pagamento"].map(meses_dict)

    grafico_comp = grafico_comp.sort_values("Mes_Pagamento")

    fig_comp = px.bar(
        grafico_comp,
        x="Mes",
        y=["Pago_2025", "Pago_2026"],
        barmode="group",
        title="Pagamentos Realizados por Mês"
    )

    fig_comp.update_layout(
        xaxis_title="Mês",
        yaxis_title="Valor Pago (R$)",
        height=500,
        legend_title_text="Ano"
    )

    st.plotly_chart(
        fig_comp,
        use_container_width=True
    )

    st.divider()

    # -----------------------------
    # Gráfico Forecast 2026
    # -----------------------------

    st.subheader("🔮 Realizado x Forecast - 2026")

    realizado_grafico = realizado_2026.rename(
        columns={"Pago_2026": "Valor"}
    )

    realizado_grafico["Tipo"] = "Realizado"

    if forecast_df.empty:
        grafico_forecast = realizado_grafico[
            ["Mes_Pagamento", "Valor", "Tipo"]
        ]
    else:
        grafico_forecast = pd.concat(
            [
                realizado_grafico[
                    ["Mes_Pagamento", "Valor", "Tipo"]
                ],
                forecast_df[
                    ["Mes_Pagamento", "Valor", "Tipo"]
                ]
            ],
            ignore_index=True
        )

    grafico_forecast["Mes"] = grafico_forecast["Mes_Pagamento"].map(meses_dict)

    grafico_forecast = grafico_forecast.sort_values("Mes_Pagamento")

    fig_forecast = px.bar(
        grafico_forecast,
        x="Mes",
        y="Valor",
        color="Tipo",
        text="Valor",
        title="Realizado e Projeção até Dezembro"
    )

    fig_forecast.update_traces(
        texttemplate="%{y:,.0f}",
        textposition="outside"
    )

    fig_forecast.update_layout(
        xaxis_title="Mês",
        yaxis_title="Valor Pago / Projetado (R$)",
        height=550
    )

    st.plotly_chart(
        fig_forecast,
        use_container_width=True
    )

    st.divider()

    # -----------------------------
    # Tabela comparativa
    # -----------------------------

    st.subheader("📋 Tabela Comparativa 2025 x 2026")

    tabela_comp = comparativo_final.copy()

    tabela_comp["Mês"] = tabela_comp["Mes_Pagamento"].map(meses_dict)

    tabela_comp["2025"] = tabela_comp["Pago_2025"].apply(formatar_valor)

    tabela_comp["2026"] = tabela_comp["Pago_2026"].apply(formatar_valor)

    tabela_comp["Variação %"] = tabela_comp["Variacao_%"].map(
        lambda x: f"{x:.1f}%".replace(".", ",")
    )

    tabela_comp = tabela_comp[
        [
            "Mês",
            "2025",
            "2026",
            "Variação %"
        ]
    ]

    st.dataframe(
        tabela_comp,
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------
    # Tabela Forecast
    # -----------------------------

    st.subheader("📋 Tabela Forecast 2026")

    tabela_forecast = grafico_forecast.copy()

    tabela_forecast["Valor"] = tabela_forecast["Valor"].apply(formatar_valor)

    tabela_forecast = tabela_forecast[
        [
            "Mes",
            "Tipo",
            "Valor"
        ]
    ]

    tabela_forecast = tabela_forecast.rename(
        columns={
            "Mes": "Mês"
        }
    )

    st.dataframe(
        tabela_forecast,
        use_container_width=True,
        hide_index=True
    )