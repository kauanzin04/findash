import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

from database import (
    initialize_database,
    load_demo_data,
    demo_data_exists,

    get_transactions,
    add_transaction,
    delete_transaction,
    delete_all_transactions,

    get_investments,
    add_investment,
    delete_investment,
    delete_all_investments,

    get_goals,
    add_goal,
    update_goal,
    delete_goal,
    delete_all_goals,

    delete_all_data,
    get_database_stats,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="FinDash",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# BANCO
# ============================================================

initialize_database()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def format_brl(value):
    """
    Formata número como moeda brasileira.
    """

    return f"R$ {value:,.2f}".replace(
        ",", "X"
    ).replace(
        ".", ","
    ).replace(
        "X", "."
    )


def format_date(value):
    """
    Converte YYYY-MM-DD para DD/MM/YYYY.
    """

    try:
        return pd.to_datetime(value).strftime("%d/%m/%Y")
    except Exception:
        return value


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("💰 FinDash")
    st.caption("Seu painel financeiro pessoal")

    st.divider()

    page = st.radio(
        "Navegação",
        [
            "📊 Dashboard",
            "💳 Transações",
            "📈 Investimentos",
            "🎯 Metas",
            "⚙️ Configurações",
        ],
    )

    st.divider()

    stats = get_database_stats()

    st.caption("Banco de dados")

    st.write(
        f"💳 {stats['transactions']} transações"
    )

    st.write(
        f"📈 {stats['investments']} investimentos"
    )

    st.write(
        f"🎯 {stats['goals']} metas"
    )

    st.divider()

    st.caption("FinDash v2.0")
    st.caption("Python • Streamlit • SQLite")


# ============================================================
# CARREGAR DADOS
# ============================================================

transactions = pd.DataFrame(get_transactions())
investments = pd.DataFrame(get_investments())
goals = pd.DataFrame(get_goals())


# ============================================================
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    st.title("📊 Dashboard")
    st.write("Visão geral da sua vida financeira.")

    st.divider()

    if transactions.empty and investments.empty and goals.empty:

        st.info(
            "Seu banco está vazio. "
            "Você pode adicionar seus próprios dados ou "
            "carregar dados de demonstração em Configurações."
        )

    # --------------------------------------------------------
    # FILTRO DE DATAS
    # --------------------------------------------------------

    if not transactions.empty:

        transactions["transaction_date"] = pd.to_datetime(
            transactions["transaction_date"]
        )

        min_date = transactions["transaction_date"].min().date()
        max_date = transactions["transaction_date"].max().date()

        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "Data inicial",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
            )

        with col2:
            end_date = st.date_input(
                "Data final",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
            )

        filtered_transactions = transactions[
            (
                transactions["transaction_date"].dt.date >= start_date
            )
            &
            (
                transactions["transaction_date"].dt.date <= end_date
            )
        ].copy()

    else:

        filtered_transactions = pd.DataFrame(
            columns=[
                "id",
                "transaction_date",
                "description",
                "category",
                "transaction_type",
                "amount",
            ]
        )

    # --------------------------------------------------------
    # MÉTRICAS
    # --------------------------------------------------------

    if not filtered_transactions.empty:

        total_income = filtered_transactions.loc[
            filtered_transactions["transaction_type"] == "Receita",
            "amount"
        ].sum()

        total_expenses = filtered_transactions.loc[
            filtered_transactions["transaction_type"] == "Despesa",
            "amount"
        ].sum()

    else:

        total_income = 0
        total_expenses = 0

    balance = total_income - total_expenses

    if not investments.empty:
        total_investments = investments["amount"].sum()
    else:
        total_investments = 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Receitas",
        format_brl(total_income)
    )

    col2.metric(
        "Despesas",
        format_brl(total_expenses)
    )

    col3.metric(
        "Saldo",
        format_brl(balance)
    )

    col4.metric(
        "Investimentos",
        format_brl(total_investments)
    )

    st.divider()

    # --------------------------------------------------------
    # GRÁFICOS
    # --------------------------------------------------------

    if not filtered_transactions.empty:

        col1, col2 = st.columns(2)

        # -------------------------
        # EVOLUÇÃO MENSAL
        # -------------------------

        with col1:

            st.subheader("📈 Evolução mensal")

            monthly = filtered_transactions.copy()

            monthly["month"] = (
                monthly["transaction_date"]
                .dt.to_period("M")
                .astype(str)
            )

            monthly_summary = (
                monthly
                .groupby(
                    ["month", "transaction_type"]
                )["amount"]
                .sum()
                .reset_index()
            )

            fig = px.line(
                monthly_summary,
                x="month",
                y="amount",
                color="transaction_type",
                markers=True,
                labels={
                    "month": "Mês",
                    "amount": "Valor",
                    "transaction_type": "Tipo",
                },
            )

            fig.update_layout(
                legend_title_text=""
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # -------------------------
        # DESPESAS POR CATEGORIA
        # -------------------------

        with col2:

            st.subheader("🍕 Despesas por categoria")

            expenses = filtered_transactions[
                filtered_transactions["transaction_type"]
                == "Despesa"
            ]

            if not expenses.empty:

                category_summary = (
                    expenses
                    .groupby("category")["amount"]
                    .sum()
                    .reset_index()
                )

                fig = px.pie(
                    category_summary,
                    names="category",
                    values="amount",
                    hole=0.45,
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.info(
                    "Nenhuma despesa encontrada."
                )

    # --------------------------------------------------------
    # CARTEIRA
    # --------------------------------------------------------

    if not investments.empty:

        st.subheader("💼 Carteira de investimentos")

        portfolio = (
            investments
            .groupby("asset_type")["amount"]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            portfolio,
            x="asset_type",
            y="amount",
            labels={
                "asset_type": "Tipo",
                "amount": "Valor",
            },
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # ÚLTIMAS TRANSAÇÕES
    # --------------------------------------------------------

    st.subheader("🧾 Últimas transações")

    if not transactions.empty:

        latest = transactions.copy()

        latest["transaction_date"] = (
            latest["transaction_date"]
            .dt.strftime("%d/%m/%Y")
        )

        latest = latest.head(8)

        latest = latest[
            [
                "transaction_date",
                "description",
                "category",
                "transaction_type",
                "amount",
            ]
        ]

        latest.columns = [
            "Data",
            "Descrição",
            "Categoria",
            "Tipo",
            "Valor",
        ]

        st.dataframe(
            latest,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("Nenhuma transação cadastrada.")


# ============================================================
# TRANSAÇÕES
# ============================================================

elif page == "💳 Transações":

    st.title("💳 Transações")
    st.write("Controle suas receitas e despesas.")

    st.divider()

    # --------------------------------------------------------
    # ADICIONAR
    # --------------------------------------------------------

    st.subheader("➕ Nova transação")

    with st.form("transaction_form"):

        col1, col2 = st.columns(2)

        with col1:

            transaction_date = st.date_input(
                "Data",
                value=date.today()
            )

            description = st.text_input(
                "Descrição",
                placeholder="Ex: Mercado"
            )

            category = st.selectbox(
                "Categoria",
                [
                    "Trabalho",
                    "Alimentação",
                    "Transporte",
                    "Moradia",
                    "Lazer",
                    "Investimentos",
                    "Educação",
                    "Saúde",
                    "Outros",
                ]
            )

        with col2:

            transaction_type = st.selectbox(
                "Tipo",
                [
                    "Receita",
                    "Despesa",
                ]
            )

            amount = st.number_input(
                "Valor",
                min_value=0.01,
                step=10.0,
                format="%.2f"
            )

        submitted = st.form_submit_button(
            "Adicionar transação",
            use_container_width=True,
        )

        if submitted:

            if not description.strip():

                st.error(
                    "Digite uma descrição."
                )

            elif amount <= 0:

                st.error(
                    "O valor precisa ser maior que zero."
                )

            else:

                add_transaction(
                    transaction_date.isoformat(),
                    description.strip(),
                    category,
                    transaction_type,
                    amount,
                )

                st.success(
                    "Transação adicionada!"
                )

                st.rerun()

    st.divider()

    # --------------------------------------------------------
    # LISTA
    # --------------------------------------------------------

    st.subheader("📋 Histórico")

    transactions = pd.DataFrame(
        get_transactions()
    )

    if transactions.empty:

        st.info(
            "Nenhuma transação cadastrada."
        )

    else:

        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:

            type_filter = st.selectbox(
                "Filtrar por tipo",
                [
                    "Todos",
                    "Receita",
                    "Despesa",
                ]
            )

        with filter_col2:

            category_options = [
                "Todas"
            ] + sorted(
                transactions["category"].unique().tolist()
            )

            category_filter = st.selectbox(
                "Filtrar por categoria",
                category_options,
            )

        filtered = transactions.copy()

        if type_filter != "Todos":

            filtered = filtered[
                filtered["transaction_type"]
                == type_filter
            ]

        if category_filter != "Todas":

            filtered = filtered[
                filtered["category"]
                == category_filter
            ]

        st.write(
            f"**{len(filtered)} transação(ões) encontrada(s)**"
        )

        for _, row in filtered.iterrows():

            col1, col2, col3, col4, col5, col6 = st.columns(
                [1.2, 2.2, 1.5, 1.2, 1.2, 0.8]
            )

            col1.write(
                format_date(row["transaction_date"])
            )

            col2.write(
                row["description"]
            )

            col3.write(
                row["category"]
            )

            col4.write(
                row["transaction_type"]
            )

            col5.write(
                format_brl(row["amount"])
            )

            if col6.button(
                "🗑️",
                key=f"delete_transaction_{row['id']}"
            ):

                delete_transaction(
                    int(row["id"])
                )

                st.rerun()


# ============================================================
# INVESTIMENTOS
# ============================================================

elif page == "📈 Investimentos":

    st.title("📈 Investimentos")
    st.write("Acompanhe sua carteira.")

    st.divider()

    investments = pd.DataFrame(
        get_investments()
    )

    # --------------------------------------------------------
    # MÉTRICAS
    # --------------------------------------------------------

    if not investments.empty:

        total = investments["amount"].sum()

        average_profitability = investments[
            "profitability"
        ].mean()

    else:

        total = 0
        average_profitability = 0

    col1, col2 = st.columns(2)

    col1.metric(
        "Patrimônio investido",
        format_brl(total)
    )

    col2.metric(
        "Rentabilidade média",
        f"{average_profitability:.2f}%"
    )

    st.divider()

    # --------------------------------------------------------
    # ADICIONAR
    # --------------------------------------------------------

    st.subheader("➕ Novo investimento")

    with st.form("investment_form"):

        col1, col2 = st.columns(2)

        with col1:

            name = st.text_input(
                "Nome",
                placeholder="Ex: CDB 110% CDI"
            )

            asset_type = st.selectbox(
                "Tipo",
                [
                    "Renda fixa",
                    "FII",
                    "Ações",
                    "ETF",
                    "Criptomoedas",
                    "Outros",
                ]
            )

            amount = st.number_input(
                "Valor investido",
                min_value=0.01,
                step=100.0,
                format="%.2f"
            )

        with col2:

            profitability = st.number_input(
                "Rentabilidade (%)",
                step=0.1,
                format="%.2f"
            )

            investment_date = st.date_input(
                "Data do investimento",
                value=date.today()
            )

        submitted = st.form_submit_button(
            "Adicionar investimento",
            use_container_width=True,
        )

        if submitted:

            if not name.strip():

                st.error(
                    "Digite o nome do investimento."
                )

            elif amount <= 0:

                st.error(
                    "O valor precisa ser maior que zero."
                )

            else:

                add_investment(
                    name.strip(),
                    asset_type,
                    amount,
                    profitability,
                    investment_date.isoformat(),
                )

                st.success(
                    "Investimento adicionado!"
                )

                st.rerun()

    st.divider()

    # --------------------------------------------------------
    # CARTEIRA
    # --------------------------------------------------------

    st.subheader("💼 Minha carteira")

    if investments.empty:

        st.info(
            "Nenhum investimento cadastrado."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:

            portfolio = (
                investments
                .groupby("asset_type")["amount"]
                .sum()
                .reset_index()
            )

            fig = px.pie(
                portfolio,
                names="asset_type",
                values="amount",
                hole=0.45,
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with col2:

            table = investments.copy()

            table["investment_date"] = (
                table["investment_date"]
                .apply(format_date)
            )

            table["amount"] = (
                table["amount"]
                .apply(format_brl)
            )

            table["profitability"] = (
                table["profitability"]
                .map(lambda x: f"{x:.2f}%")
            )

            table = table[
                [
                    "name",
                    "asset_type",
                    "amount",
                    "profitability",
                    "investment_date",
                ]
            ]

            table.columns = [
                "Nome",
                "Tipo",
                "Valor",
                "Rentabilidade",
                "Data",
            ]

            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True,
            )

        st.divider()

        st.subheader("🗑️ Remover investimento")

        for _, row in investments.iterrows():

            col1, col2, col3 = st.columns(
                [3, 2, 1]
            )

            col1.write(row["name"])
            col2.write(format_brl(row["amount"]))

            if col3.button(
                "Excluir",
                key=f"delete_investment_{row['id']}"
            ):

                delete_investment(
                    int(row["id"])
                )

                st.rerun()


# ============================================================
# METAS
# ============================================================

elif page == "🎯 Metas":

    st.title("🎯 Metas financeiras")
    st.write("Acompanhe o progresso dos seus objetivos.")

    st.divider()

    # --------------------------------------------------------
    # NOVA META
    # --------------------------------------------------------

    st.subheader("➕ Nova meta")

    with st.form("goal_form"):

        name = st.text_input(
            "Nome da meta",
            placeholder="Ex: Comprar notebook"
        )

        col1, col2 = st.columns(2)

        with col1:

            target = st.number_input(
                "Valor da meta",
                min_value=0.01,
                step=100.0,
                format="%.2f"
            )

        with col2:

            current = st.number_input(
                "Valor atual",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

        submitted = st.form_submit_button(
            "Criar meta",
            use_container_width=True,
        )

        if submitted:

            if not name.strip():

                st.error(
                    "Digite o nome da meta."
                )

            elif target <= 0:

                st.error(
                    "O objetivo precisa ser maior que zero."
                )

            elif current > target:

                st.error(
                    "O valor atual não pode ser maior que a meta."
                )

            else:

                add_goal(
                    name.strip(),
                    target,
                    current
                )

                st.success(
                    "Meta criada!"
                )

                st.rerun()

    st.divider()

    # --------------------------------------------------------
    # METAS
    # --------------------------------------------------------

    goals = pd.DataFrame(
        get_goals()
    )

    if goals.empty:

        st.info(
            "Nenhuma meta cadastrada."
        )

    else:

        for _, goal in goals.iterrows():

            target_value = float(
                goal["target"]
            )

            current_value = float(
                goal["current"]
            )

            if target_value > 0:

                progress = (
                    current_value / target_value
                )

            else:

                progress = 0

            progress = min(
                max(progress, 0),
                1
            )

            st.subheader(
                f"🎯 {goal['name']}"
            )

            st.progress(
                progress
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Atual",
                format_brl(current_value)
            )

            col2.metric(
                "Objetivo",
                format_brl(target_value)
            )

            col3.metric(
                "Progresso",
                f"{progress * 100:.1f}%"
            )

            st.write(
                f"Faltam **{format_brl(target_value - current_value)}**"
            )

            col1, col2 = st.columns([3, 1])

            with col1:

                new_value = st.number_input(
                    "Atualizar valor",
                    min_value=0.0,
                    max_value=target_value,
                    value=current_value,
                    step=100.0,
                    key=f"goal_value_{goal['id']}",
                )

            with col2:

                st.write("")

                if st.button(
                    "Atualizar",
                    key=f"update_goal_{goal['id']}"
                ):

                    update_goal(
                        int(goal["id"]),
                        new_value
                    )

                    st.success(
                        "Meta atualizada!"
                    )

                    st.rerun()

            if st.button(
                "🗑️ Excluir meta",
                key=f"delete_goal_{goal['id']}"
            ):

                delete_goal(
                    int(goal["id"])
                )

                st.rerun()

            st.divider()


# ============================================================
# CONFIGURAÇÕES
# ============================================================

elif page == "⚙️ Configurações":

    st.title("⚙️ Configurações")

    st.write(
        "Gerencie os dados armazenados no FinDash."
    )

    st.divider()

    # --------------------------------------------------------
    # ESTATÍSTICAS
    # --------------------------------------------------------

    st.subheader("📊 Banco de dados")

    stats = get_database_stats()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Transações",
        stats["transactions"]
    )

    col2.metric(
        "Investimentos",
        stats["investments"]
    )

    col3.metric(
        "Metas",
        stats["goals"]
    )

    st.divider()

    # --------------------------------------------------------
    # DEMO
    # --------------------------------------------------------

    st.subheader("🧪 Dados de demonstração")

    st.write(
        "Carregue dados fictícios para testar o dashboard."
    )

    st.warning(
        "Os dados de demonstração serão adicionados "
        "ao banco atual. Eles não substituem seus dados."
    )

    if st.button(
        "📥 Carregar dados de demonstração",
        use_container_width=True
    ):

        load_demo_data()

        st.success(
            "Dados de demonstração carregados!"
        )

        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # ZONA PERIGOSA
    # --------------------------------------------------------

    st.subheader("⚠️ Zona perigosa")

    st.warning(
        "As ações abaixo apagam dados permanentemente."
    )

    # --------------------------------------------------------
    # TRANSAÇÕES
    # --------------------------------------------------------

    if st.button(
        "🗑️ Apagar todas as transações",
        use_container_width=True
    ):

        st.session_state["confirm_transactions"] = True

    if st.session_state.get(
        "confirm_transactions",
        False
    ):

        st.error(
            "Tem certeza que deseja apagar todas as transações?"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "Sim, apagar",
                key="confirm_delete_transactions",
                use_container_width=True
            ):

                delete_all_transactions()

                st.session_state[
                    "confirm_transactions"
                ] = False

                st.success(
                    "Todas as transações foram apagadas."
                )

                st.rerun()

        with col2:

            if st.button(
                "Cancelar",
                key="cancel_delete_transactions",
                use_container_width=True
            ):

                st.session_state[
                    "confirm_transactions"
                ] = False

                st.rerun()

    # --------------------------------------------------------
    # INVESTIMENTOS
    # --------------------------------------------------------

    if st.button(
        "🗑️ Apagar todos os investimentos",
        use_container_width=True
    ):

        st.session_state["confirm_investments"] = True

    if st.session_state.get(
        "confirm_investments",
        False
    ):

        st.error(
            "Tem certeza que deseja apagar todos os investimentos?"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "Sim, apagar",
                key="confirm_delete_investments",
                use_container_width=True
            ):

                delete_all_investments()

                st.session_state[
                    "confirm_investments"
                ] = False

                st.success(
                    "Todos os investimentos foram apagados."
                )

                st.rerun()

        with col2:

            if st.button(
                "Cancelar",
                key="cancel_delete_investments",
                use_container_width=True
            ):

                st.session_state[
                    "confirm_investments"
                ] = False

                st.rerun()

    # --------------------------------------------------------
    # METAS
    # --------------------------------------------------------

    if st.button(
        "🗑️ Apagar todas as metas",
        use_container_width=True
    ):

        st.session_state["confirm_goals"] = True

    if st.session_state.get(
        "confirm_goals",
        False
    ):

        st.error(
            "Tem certeza que deseja apagar todas as metas?"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "Sim, apagar",
                key="confirm_delete_goals",
                use_container_width=True
            ):

                delete_all_goals()

                st.session_state[
                    "confirm_goals"
                ] = False

                st.success(
                    "Todas as metas foram apagadas."
                )

                st.rerun()

        with col2:

            if st.button(
                "Cancelar",
                key="cancel_delete_goals",
                use_container_width=True
            ):

                st.session_state[
                    "confirm_goals"
                ] = False

                st.rerun()

    st.divider()

    # --------------------------------------------------------
    # APAGAR TUDO
    # --------------------------------------------------------

    st.subheader("💣 Apagar tudo")

    st.write(
        "Remove todas as transações, investimentos e metas."
    )

    if st.button(
        "💣 Apagar TODOS os dados",
        use_container_width=True
    ):

        st.session_state["confirm_all"] = True

    if st.session_state.get(
        "confirm_all",
        False
    ):

        st.error(
            "ATENÇÃO: isso apagará TODOS os dados do FinDash."
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "SIM, APAGAR TUDO",
                key="confirm_delete_all",
                use_container_width=True
            ):

                delete_all_data()

                st.session_state[
                    "confirm_all"
                ] = False

                st.success(
                    "Todos os dados foram apagados."
                )

                st.rerun()

        with col2:

            if st.button(
                "Cancelar",
                key="cancel_delete_all",
                use_container_width=True
            ):

                st.session_state[
                    "confirm_all"
                ] = False

                st.rerun()


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

st.caption(
    "FinDash • Dashboard financeiro pessoal • "
    "Python + Streamlit + SQLite"
)