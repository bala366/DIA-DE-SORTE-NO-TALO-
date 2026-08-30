import re
import math
import heapq
import json
from itertools import combinations

PERIMETROS_TESTE = [30,40,50,60,70,80,90,100,120,140,160,180]
REPETIDAS_TESTE = [1,2,3,4]
MAX_BACKTEST = 500
TOP_UNIVERSO = 21
TOP_HEAP = 400

MESES = [
    "JANEIRO","FEVEREIRO","MARÇO","ABRIL",
    "MAIO","JUNHO","JULHO","AGOSTO",
    "SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"
]

def limitar(v, minimo, maximo):
    return max(minimo, min(maximo, v))

def slope(valores):
    n = len(valores)
    if n < 2:
        return 0.0
    media_x = (n - 1) / 2.0
    media_y = sum(valores) / n
    num = 0.0
    den = 0.0
    for i, y in enumerate(valores):
        dx = i - media_x
        num += dx * (y - media_y)
        den += dx * dx
    if den == 0:
        return 0.0
    return num / den

def normalizar_texto(s):
    s = s.upper().strip()
    trocas = {
        "Á":"A","À":"A","Ã":"A","Â":"A",
        "É":"E","Ê":"E","Í":"I",
        "Ó":"O","Ô":"O","Õ":"O",
        "Ú":"U","Ç":"C"
    }
    for a,b in trocas.items():
        s = s.replace(a,b)
    return s

MESES_NORMALIZADOS = {normalizar_texto(m): m for m in MESES}

def extrair_mes(texto):
    texto_norm = normalizar_texto(texto)
    for chave, original in MESES_NORMALIZADOS.items():
        if chave in texto_norm:
            return original
    return ""

def ler_historico_texto(texto_arquivo):
    historico = []
    for linha_txt in texto_arquivo.splitlines():
        texto = linha_txt.strip()
        if not texto:
            continue

        nums_txt = re.findall(r"\d+", texto)
        if len(nums_txt) < 7:
            continue

        valores = [int(x) for x in nums_txt]

        if len(valores) >= 8:
            concurso = valores[0]
            candidatos = valores[1:]
        else:
            concurso = len(historico) + 1
            candidatos = valores

        dezenas = []
        vistos = set()

        for n in candidatos:
            if 1 <= n <= 31 and n not in vistos:
                vistos.add(n)
                dezenas.append(n)
                if len(dezenas) == 7:
                    break

        if len(dezenas) != 7:
            continue

        mes = extrair_mes(texto)

        historico.append({
            "concurso": concurso,
            "dezenas": tuple(sorted(dezenas)),
            "mes": mes
        })

    if not historico:
        raise ValueError("Nenhum concurso válido encontrado.")

    historico.sort(key=lambda x: x["concurso"])
    return historico

def forca_dezena(n, janela):
    serie = [1 if n in concurso["dezenas"] else 0 for concurso in janela]
    total = len(serie)

    s10 = serie[-min(10,total):]
    s20 = serie[-min(20,total):]
    s30 = serie[-min(30,total):]

    f_total = sum(serie) / total * 100
    f30 = sum(s30) / len(s30) * 100
    f20 = sum(s20) / len(s20) * 100
    f10 = sum(s10) / len(s10) * 100

    sl_total = slope(serie)
    sl30 = slope(s30)
    sl20 = slope(s20)
    sl10 = slope(s10)

    metade = max(1, total // 2)
    primeira = serie[:metade]
    segunda = serie[metade:]

    crescimento = (
        sum(segunda) / len(segunda)
        -
        sum(primeira) / len(primeira)
    )

    pesos = list(range(1, total + 1))
    temporal = sum(v*p for v,p in zip(serie,pesos)) / sum(pesos) * 100

    atraso = total
    for distancia, valor in enumerate(reversed(serie)):
        if valor:
            atraso = distancia
            break

    bonus_atraso = 0.0
    if atraso == 0:
        bonus_atraso = 2.0
    elif atraso <= 2:
        bonus_atraso = 4.0
    elif atraso <= 5:
        bonus_atraso = 3.0
    elif atraso <= 8:
        bonus_atraso = 1.5

    score = (
        f_total * 0.12
        + f30 * 0.18
        + f20 * 0.23
        + f10 * 0.28
        + temporal * 0.15
        + limitar(sl_total * 220, -10, 10)
        + limitar(sl30 * 130, -10, 10)
        + limitar(sl20 * 120, -12, 12)
        + limitar(sl10 * 100, -15, 15)
        + limitar(crescimento * 35, -12, 12)
        + bonus_atraso
    )

    return {
        "score": score,
        "freq": f_total,
        "freq30": f30,
        "freq20": f20,
        "freq10": f10,
        "slope": sl_total,
        "slope30": sl30,
        "slope20": sl20,
        "slope10": sl10,
        "crescimento": crescimento,
        "temporal": temporal,
        "atraso": atraso
    }

def ranking_dezenas(janela):
    dados = {}
    for n in range(1, 32):
        dados[n] = forca_dezena(n, janela)

    ranking = sorted(
        range(1,32),
        key=lambda n: (
            dados[n]["score"],
            dados[n]["slope10"],
            dados[n]["slope20"],
            dados[n]["crescimento"],
            n
        ),
        reverse=True
    )
    return ranking, dados

def montar_jogo_provisorio(janela, anterior, qtd_repetidas):
    ranking, dados = ranking_dezenas(janela)
    anterior_set = set(anterior["dezenas"])

    repetidas = sorted(
        anterior_set,
        key=lambda n: (
            dados[n]["score"],
            dados[n]["slope10"],
            dados[n]["slope20"],
            n
        ),
        reverse=True
    )[:qtd_repetidas]

    qtd_novas = 7 - qtd_repetidas

    novas = [
        n for n in ranking
        if n not in anterior_set
    ][:qtd_novas]

    return tuple(sorted(repetidas + novas))

def estudar_motor(historico):
    maior = max(PERIMETROS_TESTE)
    inicio = max(maior + 1, len(historico) - MAX_BACKTEST)
    indices = range(inicio, len(historico))
    resultados = []

    for perimetro in PERIMETROS_TESTE:
        for qtd_rep in REPETIDAS_TESTE:
            q2=q3=q4=q5=q6=q7=0
            soma = 0
            testes = 0

            for indice in indices:
                if indice <= perimetro:
                    continue

                alvo = historico[indice]
                anterior = historico[indice - 1]
                janela = historico[indice-perimetro:indice]

                jogo = montar_jogo_provisorio(
                    janela,
                    anterior,
                    qtd_rep
                )

                acertos = len(set(jogo) & set(alvo["dezenas"]))

                soma += acertos
                testes += 1

                if acertos == 2: q2 += 1
                elif acertos == 3: q3 += 1
                elif acertos == 4: q4 += 1
                elif acertos == 5: q5 += 1
                elif acertos == 6: q6 += 1
                elif acertos == 7: q7 += 1

            if testes == 0:
                continue

            media = soma / testes

            score = (
                q4 * 7.0
                + q3 * 2.0
                + q5 * 3.0
                + q2 * 0.20
                + media * 4.0
            )

            resultados.append({
                "perimetro": perimetro,
                "repetidas": qtd_rep,
                "score": score,
                "q2": q2,
                "q3": q3,
                "q4": q4,
                "q5": q5,
                "q6": q6,
                "q7": q7,
                "media": media,
                "testes": testes
            })

    if not resultados:
        raise ValueError("Não foi possível aprender o motor.")

    resultados.sort(
        key=lambda x: (
            x["score"],
            x["q4"],
            x["q3"],
            x["q5"],
            x["media"],
            -x["repetidas"]
        ),
        reverse=True
    )

    return resultados[0], resultados

def escolher_repetidas(ultimo, dados_dezenas, qtd):
    ultimo_set = set(ultimo["dezenas"])

    ranking = sorted(
        ultimo_set,
        key=lambda n: (
            dados_dezenas[n]["score"],
            dados_dezenas[n]["slope10"],
            dados_dezenas[n]["slope20"],
            dados_dezenas[n]["crescimento"],
            n
        ),
        reverse=True
    )

    return tuple(sorted(ranking[:qtd]))

def analisar_jogo(jogo, janela, ultimo_set, qtd_repetidas, dados_dezenas):
    jogo_set = set(jogo)

    if len(jogo_set & ultimo_set) != qtd_repetidas:
        return None

    serie = []

    for concurso in janela:
        acertos = len(jogo_set & set(concurso["dezenas"]))

        if acertos >= 6:
            return None

        serie.append(acertos)

    qtd0 = serie.count(0)
    qtd1 = serie.count(1)
    qtd2 = serie.count(2)
    qtd3 = serie.count(3)
    qtd4 = serie.count(4)
    qtd5 = serie.count(5)

    ult5 = serie[-5:]
    ult10 = serie[-10:]
    ult20 = serie[-20:]
    ult30 = serie[-30:]

    t5 = ult5.count(3)
    t10 = ult10.count(3)
    t20 = ult20.count(3)
    t30 = ult30.count(3)

    q4_5 = ult5.count(4)
    q4_10 = ult10.count(4)
    q4_20 = ult20.count(4)
    q4_30 = ult30.count(4)

    q5_10 = ult10.count(5)
    q5_20 = ult20.count(5)

    d10 = ult10.count(2)
    d20 = ult20.count(2)
    d30 = ult30.count(2)

    qtd_blocos = min(10, len(serie))
    tam = max(1, math.ceil(len(serie) / qtd_blocos))

    duques_blocos = []
    ternos_blocos = []
    quadras_blocos = []
    quinas_blocos = []
    pontos_blocos = []

    inicio = 0
    while inicio < len(serie):
        trecho = serie[inicio:inicio+tam]

        d2 = trecho.count(2)
        d3 = trecho.count(3)
        d4 = trecho.count(4)
        d5 = trecho.count(5)

        duques_blocos.append(d2)
        ternos_blocos.append(d3)
        quadras_blocos.append(d4)
        quinas_blocos.append(d5)

        pontos_blocos.append(
            d2*1.0 + d3*4.0 + d4*12.0 + d5*16.0
        )

        inicio += tam

    blocos_com_terno = sum(1 for x in ternos_blocos if x > 0)
    blocos_com_quadra = sum(1 for x in quadras_blocos if x > 0)

    slope_total = slope(serie)
    slope30 = slope(ult30)
    slope20 = slope(ult20)
    slope10 = slope(ult10)
    slope_blocos = slope(pontos_blocos)

    metade = max(1, len(pontos_blocos)//2)

    antigos = pontos_blocos[:metade]
    recentes = pontos_blocos[metade:]

    crescimento_blocos = (
        sum(recentes) / len(recentes)
        -
        sum(antigos) / len(antigos)
    )

    subidas = sum(
        1
        for a,b in zip(pontos_blocos,pontos_blocos[1:])
        if b > a
    )

    atraso_terno = len(serie)
    for distancia, acertos in enumerate(reversed(serie)):
        if acertos == 3:
            atraso_terno = distancia
            break

    forca_media = (
        sum(dados_dezenas[n]["score"] for n in jogo) / 7
    )

    score = (
        qtd3 * 10.0
        + qtd4 * 25.0
        + qtd5 * 8.0
        + qtd2 * 1.2

        + t30 * 1.5
        + t20 * 3.0
        + t10 * 6.0
        + t5 * 9.0

        + q4_30 * 3.0
        + q4_20 * 5.0
        + q4_10 * 8.0
        + q4_5 * 12.0

        + q5_20 * 2.0
        + q5_10 * 3.0

        + d30 * 0.5
        + d20 * 1.0
        + d10 * 1.5

        + blocos_com_terno * 4.0
        + blocos_com_quadra * 6.0

        + limitar(slope_total * 30, -8, 8)
        + limitar(slope30 * 40, -10, 10)
        + limitar(slope20 * 50, -12, 12)
        + limitar(slope10 * 60, -15, 15)
        + limitar(slope_blocos * 8, -20, 20)
        + limitar(crescimento_blocos * 2, -20, 20)

        + subidas * 2.0
        + forca_media * 0.15
    )

    if atraso_terno == 0:
        score += 10.0
    elif atraso_terno <= 2:
        score += 7.0
    elif atraso_terno <= 5:
        score += 4.0

    return {
        "jogo": tuple(sorted(jogo)),
        "score": score,
        "serie": serie,
        "qtd0": qtd0,
        "qtd1": qtd1,
        "qtd2": qtd2,
        "qtd3": qtd3,
        "qtd4": qtd4,
        "qtd5": qtd5,
        "qtd6": 0,
        "qtd7": 0,
        "ternos5": t5,
        "ternos10": t10,
        "ternos20": t20,
        "ternos30": t30,
        "quadras5": q4_5,
        "quadras10": q4_10,
        "quadras20": q4_20,
        "quadras30": q4_30,
        "quinas10": q5_10,
        "quinas20": q5_20,
        "duques10": d10,
        "duques20": d20,
        "duques30": d30,
        "duques_blocos": duques_blocos,
        "ternos_blocos": ternos_blocos,
        "quadras_blocos": quadras_blocos,
        "quinas_blocos": quinas_blocos,
        "pontos_blocos": pontos_blocos,
        "blocos_com_terno": blocos_com_terno,
        "blocos_com_quadra": blocos_com_quadra,
        "slope_total": slope_total,
        "slope30": slope30,
        "slope20": slope20,
        "slope10": slope10,
        "slope_blocos": slope_blocos,
        "crescimento_blocos": crescimento_blocos,
        "subidas": subidas,
        "atraso_terno": atraso_terno,
        "forca_media": forca_media
    }

def gerar_jogo_final(janela, ultimo, ranking, dados_dezenas, qtd_repetidas):
    ultimo_set = set(ultimo["dezenas"])

    repetidas = escolher_repetidas(
        ultimo,
        dados_dezenas,
        qtd_repetidas
    )

    qtd_novas = 7 - qtd_repetidas

    fora = [
        n for n in ranking
        if n not in ultimo_set
    ]

    universo_futuras = fora[:TOP_UNIVERSO]

    heap = []

    for novas in combinations(universo_futuras, qtd_novas):
        jogo = tuple(sorted(repetidas + novas))

        dados = analisar_jogo(
            jogo,
            janela,
            ultimo_set,
            qtd_repetidas,
            dados_dezenas
        )

        if dados is None:
            continue

        chave = (
            dados["qtd4"],
            dados["qtd3"],
            dados["blocos_com_terno"],
            dados["quadras20"],
            dados["quadras10"],
            dados["ternos20"],
            dados["ternos10"],
            dados["ternos5"],
            dados["qtd5"],
            dados["qtd2"],
            dados["slope_blocos"],
            dados["crescimento_blocos"],
            dados["score"],
            dados["jogo"]
        )

        item = (chave, dados)

        if len(heap) < TOP_HEAP:
            heapq.heappush(heap, item)
        elif chave > heap[0][0]:
            heapq.heapreplace(heap, item)

    if not heap:
        raise ValueError("Nenhum jogo passou pela trava 6/7.")

    melhores = sorted(
        heap,
        key=lambda x: x[0],
        reverse=True
    )

    return repetidas, melhores[0][1]

def escolher_mes_da_sorte(janela):
    meses_presentes = [
        concurso["mes"]
        for concurso in janela
        if concurso["mes"]
    ]

    if not meses_presentes:
        return {
            "mes":"NÃO IDENTIFICADO",
            "score":0.0,
            "freq":0,
            "freq20":0,
            "freq10":0,
            "slope":0.0
        }

    ranking = []

    for mes in MESES:
        serie = [
            1 if concurso["mes"] == mes else 0
            for concurso in janela
        ]

        total = len(serie)
        s20 = serie[-min(20,total):]
        s10 = serie[-min(10,total):]

        freq = sum(serie)
        freq20 = sum(s20)
        freq10 = sum(s10)

        sl = slope(serie)
        sl20 = slope(s20)
        sl10 = slope(s10)

        pesos = list(range(1,total+1))

        temporal = (
            sum(v*p for v,p in zip(serie,pesos))
            /
            sum(pesos)
            *
            100
        )

        score = (
            freq * 1.0
            + freq20 * 3.0
            + freq10 * 5.0
            + temporal * 0.35
            + limitar(sl * 100, -8, 8)
            + limitar(sl20 * 100, -10, 10)
            + limitar(sl10 * 100, -12, 12)
        )

        ranking.append({
            "mes": mes,
            "score": score,
            "freq": freq,
            "freq20": freq20,
            "freq10": freq10,
            "slope": sl,
            "slope20": sl20,
            "slope10": sl10
        })

    ranking.sort(
        key=lambda x: (
            x["score"],
            x["freq10"],
            x["freq20"],
            x["freq"],
            x["mes"]
        ),
        reverse=True
    )

    return ranking[0]

def executar_texto(texto):
    historico = ler_historico_texto(texto)

    if len(historico) < max(PERIMETROS_TESTE) + 2:
        raise ValueError("Histórico insuficiente.")

    motor, tabela = estudar_motor(historico)

    perimetro = motor["perimetro"]
    qtd_repetidas = motor["repetidas"]

    janela = historico[-perimetro:]
    ultimo = historico[-1]

    ranking, dados_dezenas = ranking_dezenas(janela)

    repetidas, melhor = gerar_jogo_final(
        janela,
        ultimo,
        ranking,
        dados_dezenas,
        qtd_repetidas
    )

    mes_sorte = escolher_mes_da_sorte(janela)

    ultimo_set = set(ultimo["dezenas"])
    novas = [
        n for n in melhor["jogo"]
        if n not in ultimo_set
    ]

    out = dict(melhor)

    out["jogo"] = list(melhor["jogo"])
    out["repetidas"] = list(repetidas)
    out["novas"] = list(novas)

    out["perimetro"] = perimetro
    out["qtd_repetidas"] = qtd_repetidas
    out["primeiro_concurso_perimetro"] = janela[0]["concurso"]
    out["ultimo_concurso"] = ultimo["concurso"]
    out["ultimo_resultado"] = list(ultimo["dezenas"])
    out["ultimo_mes"] = ultimo["mes"]

    out["motor"] = motor
    out["tabela_motor"] = tabela
    out["mes_sorte"] = mes_sorte

    out["identificacao"] = "DIA_DE_SORTE_ENGROSSANDO_TALO_V1"

    return json.dumps(out, ensure_ascii=False)
