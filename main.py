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

# --- FUNÇÃO DE ANÁLISE (ESCANTEIOS HT + OVER GOLS 2H) ---
def analisar_estatisticas(fixture_id, home_team, away_team, minuto, gols_casa, gols_fora, tempo):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=HEADERS).json()

        if not response.get('response') or len(response['response']) < 2:
            return

        # Organiza os dados estatísticos de cada time
        stats_casa = {item['type']: item['value'] for item in response['response'][0]['statistics']}
        stats_fora = {item['type']: item['value'] for item in response['response'][1]['statistics']}

        # Puxa os dados necessários (garantindo que se for None vire 0)
        escanteios_casa = stats_casa.get('Corner Kicks') or 0
        escanteios_fora = stats_fora.get('Corner Kicks') or 0
        
        chutes_no_gol_casa = stats_casa.get('Shots on Goal') or 0
        chutes_no_gol_fora = stats_fora.get('Shots on Goal') or 0
        
        chutes_fora_casa = stats_casa.get('Shots off Goal') or 0
        chutes_fora_fora = stats_fora.get('Shots off Goal') or 0
        
        chutes_totais_casa = chutes_no_gol_casa + chutes_fora_casa
        chutes_totais_fora = chutes_no_gol_fora + chutes_fora_fora

        # Trata a posse de bola (remove o símbolo de % se vier como texto)
        posse_casa = stats_casa.get('Ball Possession') or "0%"
        posse_fora = stats_fora.get('Ball Possession') or "0%"
        if isinstance(posse_casa, str): posse_casa = int(posse_casa.replace('%', ''))
        if isinstance(posse_fora, str): posse_fora = int(posse_fora.replace('%', ''))

        # =========================================================================
        # STRATEGY 1: FUNIL DE ESCANTEIOS HT (1º TEMPO - 25' a 38')
        # =========================================================================
        if tempo == "1H" and 25 <= minuto <= 38:
            # Casa Pressionando
            if (gols_casa == gols_fora or gols_fora - gols_casa == 1) and chutes_totais_casa >= 5 and escanteios_casa >= 3:
                msg = (
                    f"🔥 **ALERTA: ESCANTEIOS HT** 🔥\n\n"
                    f"⚽ **{home_team}** x {away_team}\n"
                    f"⏱️ Placar: {gols_casa}x{gols_fora} ({minuto}' 1ºT)\n"
                    f"🎯 **Pressão:** {home_team} (Casa)\n\n"
                    f"📊 **Estatísticas:**\n"
                    f"• Escanteios do time: {escanteios_casa}\n"
                    f"• Total de Chutes: {chutes_totais_casa}\n\n"
                    f"💡 *Sugestão: Over Cantos Limite HT!*"
                )
                enviar_telegram(msg)
                time.sleep(2)

            # Fora Pressionando
            elif (gols_casa == gols_fora or gols_casa - gols_fora == 1) and chutes_totais_fora >= 5 and escanteios_fora >= 3:
                msg = (
                    f"🔥 **ALERTA: ESCANTEIOS HT** 🔥\n\n"
                    f"⚽ {home_team} x **{away_team}**\n"
                    f"⏱️ Placar: {gols_casa}x{gols_fora} ({minuto}' 1ºT)\n"
                    f"🎯 **Pressão:** {away_team} (Fora)\n\n"
                    f"📊 **Estatísticas:**\n"
                    f"• Escanteios do time: {escanteios_fora}\n"
                    f"• Total de Chutes: {chutes_totais_fora}\n\n"
                    f"💡 *Sugestão: Over Cantos Limite HT!*"
                )
                enviar_telegram(msg)
                time.sleep(2)

        # =========================================================================
        # STRATEGY 2: PRESSÃO DO FAVORITO / OVER GOLS (2º TEMPO - 60' a 75')
        # =========================================================================
        elif tempo == "2H" and 60 <= minuto <= 75:
            # Cenário A: Time da Casa amassando (Empatado ou Perdendo por 1 gol) + Posse > 60% + Pelo menos 8 chutes
            if (gols_casa == gols_fora or gols_fora - gols_casa == 1) and posse_casa >= 60 and chutes_totais_casa >= 8:
                msg = (
                    f"🚨 **ALERTA: PRESSÃO FAVORITO (OVER GOLS)** 🚨\n\n"
                    f"⚽ **{home_team}** x {away_team}\n"
                    f"⏱️ Placar: {gols_casa}x{gols_fora} ({minuto}' 2ºT)\n"
                    f"🎯 **Sufoco da Casa:** {home_team}\n\n"
                    f"📊 **Estatísticas de Pressão:**\n"
                    f"• Posse de Bola: {posse_casa}%\n"
                    f"• Chutes Totais: {chutes_totais_casa} (No gol: {chutes_no_gol_casa})\n"
                    f"• Escanteios: {escanteios_casa}\n\n"
                    f"💡 *Sugestão: Buscar Over 1.5 Gols ou Gol Limite na partida!*"
                )
                enviar_telegram(msg)
                time.sleep(2)

            # Cenário B: Time de Fora amassando (Empatado ou Perdendo por 1 gol) + Posse > 60% + Pelo menos 8 chutes
            elif (gols_casa == gols_fora or gols_casa - gols_fora == 1) and posse_fora >= 60 and chutes_totais_fora >= 8:
                msg = (
                    f"🚨 **ALERTA: PRESSÃO FAVORITO (OVER GOLS)** 🚨\n\n"
                    f"⚽ {home_team} x **{away_team}**\n"
                    f"⏱️ Placar: {gols_casa}x{gols_fora} ({minuto}' 2ºT)\n"
                    f"🎯 **Sufoco de Fora:** {away_team}\n\n"
                    f"📊 **Estatísticas de Pressão:**\n"
                    f"• Posse de Bola: {posse_fora}%\n"
                    f"• Chutes Totais: {chutes_totais_fora} (No gol: {chutes_no_gol_fora})\n"
                    f"• Escanteios: {escanteios_fora}\n\n"
                    f"💡 *Sugestão: Buscar Over 1.5 Gols ou Gol Limite na partida!*"
                )
                enviar_telegram(msg)
                time.sleep(2)

    except Exception as e:
        print(f"Erro ao buscar estatísticas do jogo {fixture_id}: {e}")

# --- LOOP PRINCIPAL ---
def monitorar_jogos_ao_vivo():
    print("🤖 Robô de Escanteios e Gols Iniciado...")
    url_live = "https://v3.football.api-sports.io/fixtures?live=all"

    while True:
        print("Buscando novos jogos ao vivo...")
        try:
            response = requests.get(url_live, headers=HEADERS).json()
            jogos = response.get('response', [])

            if not jogos:
                print("Nenhum jogo ao vivo rolando agora. Próxima checagem em 2 minutos...")

            for jogo in jogos:
                status = jogo['fixture']['status']['short']
                minuto = jogo['fixture']['status']['elapsed'] or 0

                # Captura tanto jogos do Primeiro Tempo (1H) quanto do Segundo Tempo (2H)
                if status in ["1H", "2H"]:
                    fixture_id = jogo['fixture']['id']
                    home_team = jogo['teams']['home']['name']
                    away_team = jogo['teams']['away']['name']
                    gols_casa = jogo['goals']['home'] or 0
                    gols_fora = jogo['goals']['away'] or 0

                    # Dispara a análise passando o tempo atual (1H ou 2H)
                    analisar_estatisticas(fixture_id, home_team, away_team, minuto, gols_casa, gols_fora, status)
                    time.sleep(1)

            time.sleep(120)

        except Exception as e:
            print(f"Erro no monitoramento geral: {e}")
            time.sleep(60)

if __name__ == "__main__":
    # MENSAGEM DE TESTE IMEDIATA: Garante que o bot consegue falar com seu Telegram
    enviar_telegram("🚀 **O robô foi iniciado com sucesso!**\nA partir de agora estou monitorando o mercado HT de escanteios e 2H de gols.")
    
    monitorar_jogos_ao_vivo()
