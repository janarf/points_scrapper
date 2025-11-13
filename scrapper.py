import requests
from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import re
from datetime import date

def scrape_livelo():
    url = "https://www.livelo.com.br/juntar-pontos/todos-os-parceiros"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    cards = soup.select('[data-testid="a_PartnerCard_card_link"]')

    data = []
    today = date.today().isoformat()  # YYYY-MM-DD

    for card in cards:
        # Nome do parceiro
        img = card.select_one('[data-testid="img_PartnerCard_partnerImage"]')
        nome = img.get("alt").replace("Logo ", "").strip() if img and img.get("alt") else None

        # Extrair textos
        text_blocks = card.select('[data-testid="Text_Typography"]')
        pontos = None
        por_reais = None

        for i, div in enumerate(text_blocks):
            text = div.get_text(strip=True)
            if "ponto" in text.lower() and i > 0:
                pontos = text_blocks[i - 1].get_text(strip=True)
                
                # Procurar "por R$" ou "por U$" nos irmãos seguintes
                sibling_texts = []
                for sibling in div.next_siblings:
                    if isinstance(sibling, NavigableString):
                        sibling_texts.append(sibling.strip())
                    elif hasattr(sibling, "get_text"):
                        sibling_texts.append(sibling.get_text(strip=True))
                combined = " ".join(sibling_texts)
                match = re.search(r"por\s*(R\$|U\$)\s*([\d,\.]+)", combined)
                if match:
                    por_reais = match.group(0)
                break

        if nome:
            data.append({
                "nome": nome,
                "pontos": pontos,
                "por_reais": por_reais,
                "scraping_day": today
            })

    df = pd.DataFrame(data)

    # --- TRANSFORMAÇÕES ---
    def parse_por_reais(text):
        if text:
            # Remove prefixos "por R$ 1" ou "por "
            text = re.sub(r"^por\s*(R\$|U\$)?\s*", "", text)
            match = re.search(r"(R\$|U\$)?\s*([\d,\.]+)", text)
            if match:
                moeda = match.group(1) if match.group(1) else "R$"  # Assume R$ se moeda não for especificada
                valor = match.group(2).replace(',', '.')  # vírgula → ponto
                return moeda, float(valor)
        return None, None

    df[['moeda', 'valor']] = df['por_reais'].apply(lambda x: pd.Series(parse_por_reais(x)))

    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    df['pontos'] = pd.to_numeric(df['pontos'], errors='coerce')

    # Ajuste USD → BRL
    exchange_rate_usd_to_brl = 5.5
    df['adjusted_valor'] = df.apply(
        lambda row: row['valor'] * exchange_rate_usd_to_brl if row['moeda'] == 'U$' else row['valor'],
        axis=1
    )

    # Pontos por real
    df['pontos_por_real'] = df['pontos'] / df['adjusted_valor']

    # Remove coluna antiga
    df = df.drop(columns=['por_reais'])

    # Ordena por nome
    df = df.sort_values("nome").reset_index(drop=True)

    return df

# Teste rápido
if __name__ == "__main__":
    df = scrape_livelo()
    print(df.head())
