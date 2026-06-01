import requests
import time

# --- CONFIGURAÇÕES DO SEU ROBÔ ---
API_KEY = "7238b0f8fc6dbc7a18c9d817c34abc53"
TELEGRAM_TOKEN = "8737473531:AAH5gpMkQbiNtm2Ms8ffePck9m_cNJbcE84"
CHAT_ID = "8048641809"

HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

# --- FUNÇÃO PARA ENVIAR ALERTA PRO TELEGRAM ---
def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Erro ao enviar para o Telegram: {response.text}")
    except Exception as e:
        print(f"Erro de conexão com Telegram: {e}")

# --- FUNÇÃO QUE ACESSA O SEU LINK DE ESTATÍSTICAS ---
def analisar_estatisticas(fixture_id, home_team, away_team, minuto, gols_casa, gols_fora):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=HEADERS).json()

        if not response.get('response') or len(response['response']) < 2:
            return

        # Organiza os dados estatísticos de cada time
        stats_casa = {item['type']: item['value'] for item in response['response'][0]['statistics']}
        stats_fora = {item['type']: item['value'] for item in response['response'][1]['statistics']}

        # Puxa os Escanteios (Corner Kicks)
        escanteios_casa = stats_casa.get('Corner Kicks') or 0
        escanteios_fora = stats_fora.get('Corner Kicks') or 0

        # Puxa os Chutes (Ao gol + Para fora) para medir a pressão
        chutes_casa = (stats_casa.get('Shots on Goal') or 0) + (stats_casa.get('Shots off Goal') or 0)
        chutes_fora = (stats_fora.get('Shots on Goal') or 0) + (stats_fora.get('Shots off Goal') or 0)

        # --- FILTRO DO FUNIL: 1º TEMPO (25' a 38') ---
        if 25 <= minuto <= 38:

            # Cenário 1: Time da Casa pressionando (Empatado ou Perdendo por 1 gol)
            if (gols_casa == gols_fora or gols_fora - gols_casa == 1) and chutes_casa >= 5 and escanteios_casa >= 3:
                msg = (
                    f"🔥 **ALERTA: ESCANTEIOS HT** 🔥\n\n"
                    f"⚽ **{home_team}** x {away_team}\n"
                    f"⏱️ Placar: {gols_casa}x{gols_fora} ({minuto}' 1ºT)\n"
                    f"🎯 **Pressão:** {home_team} (Casa)\n\n"
                    f"📊 **Estatísticas:**\n"
                    f"• Escanteios do time: {escanteios_casa}\n"
                    f"• Total de Chutes: {chutes_casa}\n\n"
                    f"💡 *Sugestão: Over Cantos Limite HT!*"
                )
                enviar_telegram(msg)
                time.sleep(2)

            # Cenário 2: Time de Fora pressionando (Empatado ou Perdendo por 1 gol)
            elif (gols_casa == gols_fora or gols_casa - gols_fora == 1) and chutes_fora >= 5 and escanteios_fora >= 3:
                msg = (
                    f"🔥 **ALERTA: ESCANTEIOS HT** 🔥\n\n"
                    f"⚽ {home_team} x **{away_team}**\n"
                    f"⏱️ Placar: {gols_casa}x{gols_fora} ({minuto}' 1ºT)\n"
                    f"🎯 **Pressão:** {away_team} (Fora)\n\n"
                    f"📊 **Estatísticas:**\n"
                    f"• Escanteios do time: {escanteios_fora}\n"
                    f"• Total de Chutes: {chutes_fora}\n\n"
                    f"💡 *Sugestão: Over Cantos Limite HT!*"
                )
                enviar_telegram(msg)
                time.sleep(2)

    except Exception as e:
        print(f"Erro ao buscar estatísticas do jogo {fixture_id}: {e}")

# --- LOOP PRINCIPAL (Roda procurando jogos ao vivo) ---
def monitorar_jogos_ao_vivo():
    print("🤖 Robô de Escanteios Iniciado e Monitorando os Jogos...")
    url_live = "https://v3.football.api-sports.io/fixtures?live=all"

    while True:
        print("Buscando novos jogos ao vivo...")  # Linha importante para ver no log do GitHub
        try:
            response = requests.get(url_live, headers=HEADERS).json()
            jogos = response.get('response', [])

            if not jogos:
                print("Nenhum jogo ao vivo rolando agora. Próxima checagem em 2 minutos...")

            # CORRIGIDO: de 'jobs' para 'jogos'
            for jogo in jogos:
                status = jogo['fixture']['status']['short']
                minuto = jogo['fixture']['status']['elapsed'] or 0

                # Foca apenas no Primeiro Tempo ("1H")
                if status == "1H":
                    fixture_id = jogo['fixture']['id']
                    home_team = jogo['teams']['home']['name']
                    away_team = jogo['teams']['away']['name']
                    gols_casa = jogo['goals']['home'] or 0
                    gols_fora = jogo['goals']['away'] or 0

                    # Analisa o jogo de perto puxando as estatísticas na URL
                    analisar_estatisticas(fixture_id, home_team, away_team, minuto, gols_casa, gols_fora)
                    time.sleep(1) # Pausa de segurança

            # Espera 2 minutos antes de verificar os jogos ao vivo novamente
            time.sleep(120)

        except Exception as e:
            print(f"Erro no monitoramento geral: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitorar_jogos_ao_vivo()
