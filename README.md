# lf_analyzer
Analisador dos resultados da Lotofacil

Funcionalidades:
Jogo 1 - Números Mais Sorteados
Analisa o histórico completo e seleciona os 15 números que mais apareceram.
Jogo 2 - Números Menos Sorteados
Seleciona os 15 números que menos apareceram no histórico.
Jogo 3 - Probabilidade por Padrão (o mais interessante!)
Este analisa para cada número:

Sequências de presença: quantos sorteios seguidos costuma aparecer
Sequências de ausência: quantos sorteios fica sem aparecer
Situação atual: está aparecendo ou ausente agora?
Calcula um score baseado em:

Se está "devendo" aparecer (passou do tempo médio ausente)
Se está em uma sequência esperada de aparições
Frequência histórica geral

📊 Novos Jogos Adicionados:
Jogo 4 - Equilíbrio Pares/Ímpares

Analisa a distribuição histórica de pares e ímpares
Raramente saem 15 pares ou 15 ímpares
Identifica o equilíbrio mais comum (ex: 8 pares e 7 ímpares)
Seleciona os números mais frequentes respeitando essa proporção

Jogo 5 - Análise de Repetições

Estuda quantos números costumam repetir entre sorteios consecutivos
Calcula a média histórica de repetições
Combina números do último sorteio (mais prováveis de repetir) com números novos mais frequentes

Jogo 6 - Distribuição Espacial

Divide os 25 números em 5 faixas (1-5, 6-10, 11-15, 16-20, 21-25)
Analisa quantos números de cada faixa aparecem em média
Evita concentração em poucas faixas (padrão raro)
Distribui os números proporcionalmente entre todas as faixas

Jogo 7 - Scoring Multifatorial ⭐ (O MAIS COMPLETO)
Sistema de pontuação que combina:

25% - Frequência histórica geral
30% - Tendência recente (últimos 50 jogos)
25% - Análise de padrões de sequência
20% - Números "quentes" (últimos 5 sorteios)

Este é um modelo híbrido que pondera diferentes critérios estatísticos!
🎯 Por que esses critérios são relevantes:

Equilíbrio: Jogos muito extremos (todos pares, todos de uma faixa) são estatisticamente raros
Repetições: Há padrões de quantos números tendem a repetir
Distribuição: Números costumam aparecer distribuídos pelo volante
Multifatorial: Combina múltiplas análises para decisão mais robusta

Agora é só:

Salvar seu arquivo CSV completo (por exemplo: lotofacil.csv)
Executar o código:
''' python lotofacil_analyzer.py '''