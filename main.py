import requests
import time

# --- CONFIGURAÇÕES DO SEU ROBÔ ---
# REGENERE ESTAS CHAVES ANTES DE USAR!
API_KEY = "SUA_NOVA_API_KEY_AQUI"
TELEGRAM_TOKEN = "SEU_NOVO_TOKEN_DO_TELEGRAM_AQUI"
CHAT_ID = "8048641809"

HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro de conexão com Telegram: {e}")

def analisar_estatisticas(fixture_id, home_team, away_team, minuto, gols_casa, gols_fora):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=HEADERS).json()
        if not response.get('response') or len(response['response']) < 2:
            return
        stats_casa = {item['type']: item['value'] for item in response['response'][0]['statistics']}
        stats_fora = {item['type']: item['value'] for item in response['response'][1]['statistics']}
        escanteios_casa = stats_casa.get('Corner Kicks') or 0
        escanteios_fora = stats_fora.get('Corner Kicks') or 0
        chutes_casa = (stats_casa.get('Shots on Goal') or 0) + (stats_casa.get('Shots off Goal') or 0)
        chutes_fora = (stats_fora.get('Shots on Goal') or 0) + (stats_fora.get('Shots off Goal') or 0)
        
        if 25 <= minuto <= 38:
            if (gols_casa == gols_fora or gols_fora - gols_casa == 1) and chutes_casa >= 5 and escanteios_casa >= 3:
                msg = f"🔥 ALERTA: ESCANTEIOS HT 🔥\n\n⚽ {home_team} x {away_team}\n⏱️ {minuto}' 1ºT\n🎯 Pressão: {home_team}"
                enviar_telegram(msg)
            elif (gols_casa == gols_fora or gols_casa - gols_fora == 1) and chutes_fora >= 5 and escanteios_fora >= 3:
                msg = f"🔥 ALERTA: ESCANTEIOS HT 🔥\n\n⚽ {home_team} x {away_team}\n⏱️ {minuto}' 1ºT\n🎯 Pressão: {away_team}"
                enviar_telegram(msg)
    except Exception as e:
        print(f"Erro: {e}")

def monitorar_jogos_ao_vivo():
    print("🤖 Robô de Escanteios Iniciado...")
    url_live = "https://v3.football.api-sports.io/fixtures?live=all"
    while True:
        print("Buscando jogos agora...") # Linha de teste para o log
        try:
            response = requests.get(url_live, headers=HEADERS).json()
            jogos = response.get('response', [])
            for jogo in jogos:
                if jogo['fixture']['status']['short'] == "1H":
                    analisar_estatisticas(jogo['fixture']['id'], jogo['teams']['home']['name'], jogo['teams']['away']['name'], jogo['fixture']['status']['elapsed'] or 0, jogo['goals']['home'] or 0, jogo['goals']['away'] or 0)
            time.sleep(120)
        except Exception as e:
            print(e)
            time.sleep(60)

if __name__ == "__main__":
    monitorar_jogos_ao_vivo()
