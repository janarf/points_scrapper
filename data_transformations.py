import pandas as pd

def transform_data(df):
    """
    Realiza as transformações necessárias no DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame original carregado.

    Returns:
        pd.DataFrame: DataFrame transformado com colunas ajustadas e cálculos realizados.
    """
    # Ajusta dinamicamente o número de colunas para corresponder ao esperado
    expected_columns = ["nome", "pontos", "moeda", "valor", "scraping_day"]
    df = df.iloc[:, :len(expected_columns)]  # Trunca colunas extras
    if len(df.columns) < len(expected_columns):
        for i in range(len(df.columns), len(expected_columns)):
            df[f"missing_{i}"] = None  # Adiciona colunas ausentes com valores nulos

    df.columns = expected_columns

    # Converte os tipos de dados
    df["pontos"] = pd.to_numeric(df["pontos"], errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["scraping_day"] = pd.to_datetime(df["scraping_day"], errors="coerce")

    # Converte valores de dólar para real, se a moeda for U$
    exchange_rate_usd_to_brl = 5.5
    df["valor"] = df.apply(
        lambda row: row["valor"] * exchange_rate_usd_to_brl if row["moeda"] == "U$" else row["valor"],
        axis=1
    )

    # Calcula pontos por real
    df["pontos_por_real"] = df["pontos"] / df["valor"]

    # Calcula a média dos dias anteriores e compara com o dia mais recente
    most_recent_day = df["scraping_day"].max()
    previous_days_mean = df[df["scraping_day"] < most_recent_day].groupby("nome")["pontos_por_real"].mean()

    def compare_with_mean(row):
        if row["scraping_day"] == most_recent_day:
            mean_value = previous_days_mean.get(row["nome"], None)
            if mean_value is not None:
                if row["pontos_por_real"] > mean_value:
                    return "📈 Subiu"
                elif row["pontos_por_real"] < mean_value:
                    return "📉 Desceu"
                else:
                    return "➖ Manteve"
        return None

    df["indicador"] = df.apply(compare_with_mean, axis=1)

    return df