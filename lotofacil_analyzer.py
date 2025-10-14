import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime

class AnalisadorLotofacil:
    def __init__(self, arquivo_csv):
        """
        Inicializa o analisador com o histórico de jogos.
        
        Args:
            arquivo_csv: Caminho para o arquivo CSV com histórico
                        Formato esperado: colunas com os 15 números sorteados
        """
        # Lê CSV com separador ponto e vírgula
        self.df = pd.read_csv(arquivo_csv, sep=';', encoding='latin-1')
        self.todos_numeros = range(1, 26)  # Lotofácil: 1 a 25
        self.historico_numeros = self._extrair_historico()
        
    def _extrair_historico(self):
        """Extrai o histórico de números sorteados em ordem cronológica."""
        historico = []
        # Pega apenas as colunas das bolas (Bola1 a Bola15)
        colunas_bolas = [f'Bola{i}' for i in range(1, 16)]
        
        for _, row in self.df.iterrows():
            try:
                # Extrai apenas as 15 bolas sorteadas
                numeros = [int(row[col]) for col in colunas_bolas if col in row]
                if len(numeros) == 15:  # Garante que tem 15 números
                    historico.append(sorted(numeros))
            except (ValueError, KeyError) as e:
                continue  # Ignora linhas com problemas
        
        return historico
    
    def jogo_mais_sorteados(self):
        """
        Jogo 1: 15 números mais sorteados no histórico.
        
        Returns:
            lista com os 15 números mais frequentes
        """
        todos = [num for jogo in self.historico_numeros for num in jogo]
        contador = Counter(todos)
        mais_sorteados = [num for num, _ in contador.most_common(15)]
        
        print("\n=== JOGO 1: NÚMEROS MAIS SORTEADOS ===")
        print(f"Números: {sorted(mais_sorteados)}")
        for num in sorted(mais_sorteados):
            print(f"  Número {num:2d}: {contador[num]:4d} vezes")
        
        return sorted(mais_sorteados)
    
    def jogo_menos_sorteados(self):
        """
        Jogo 2: 15 números menos sorteados no histórico.
        
        Returns:
            lista com os 15 números menos frequentes
        """
        todos = [num for jogo in self.historico_numeros for num in jogo]
        contador = Counter(todos)
        menos_sorteados = [num for num, _ in contador.most_common()[-15:]]
        
        print("\n=== JOGO 2: NÚMEROS MENOS SORTEADOS ===")
        print(f"Números: {sorted(menos_sorteados)}")
        for num in sorted(menos_sorteados):
            print(f"  Número {num:2d}: {contador[num]:4d} vezes")
        
        return sorted(menos_sorteados)
    
    def _analisar_padroes_numero(self, numero):
        """
        Analisa o padrão de aparição de um número específico.
        
        Args:
            numero: número a ser analisado (1-25)
            
        Returns:
            dict com estatísticas do padrão
        """
        aparicoes = []
        sequencias_presente = []
        sequencias_ausente = []
        
        # Registra quando o número aparece (1) ou não (0)
        for jogo in self.historico_numeros:
            aparicoes.append(1 if numero in jogo else 0)
        
        # Calcula sequências de presença e ausência
        seq_atual = 0
        em_sequencia_presente = aparicoes[0] == 1
        
        for presente in aparicoes:
            if presente == 1:
                if em_sequencia_presente:
                    seq_atual += 1
                else:
                    if seq_atual > 0:
                        sequencias_ausente.append(seq_atual)
                    seq_atual = 1
                    em_sequencia_presente = True
            else:
                if not em_sequencia_presente:
                    seq_atual += 1
                else:
                    if seq_atual > 0:
                        sequencias_presente.append(seq_atual)
                    seq_atual = 1
                    em_sequencia_presente = False
        
        # Adiciona última sequência
        if seq_atual > 0:
            if em_sequencia_presente:
                sequencias_presente.append(seq_atual)
            else:
                sequencias_ausente.append(seq_atual)
        
        # Verifica a situação atual (sequência de presença ou ausência no final do histórico)
        sorteios_sem_aparecer = 0
        sorteios_aparecendo = 0
        apareceu_ultimo = aparicoes[-1] == 1 if aparicoes else False

        if apareceu_ultimo:
            # Se apareceu no último, conta a sequência atual de aparições
            for presente in reversed(aparicoes):
                if presente == 1: sorteios_aparecendo += 1
                else: break
        else:
            # Se não apareceu, conta a sequência atual de ausências
            for presente in reversed(aparicoes):
                if presente == 0: sorteios_sem_aparecer += 1
                else: break
        
        return {
            'numero': numero,
            'total_aparicoes': sum(aparicoes),
            'media_seq_presente': np.mean(sequencias_presente) if sequencias_presente else 0,
            'media_seq_ausente': np.mean(sequencias_ausente) if sequencias_ausente else 0,
            'max_seq_presente': max(sequencias_presente) if sequencias_presente else 0,
            'max_seq_ausente': max(sequencias_ausente) if sequencias_ausente else 0,
            'sorteios_sem_aparecer': sorteios_sem_aparecer,
            'sorteios_aparecendo': sorteios_aparecendo,
            'apareceu_ultimo': apareceu_ultimo
        }
    
    def calcular_probabilidade_proximo(self, stats):
        """
        Calcula probabilidade do número sair no próximo sorteio baseado em padrões.
        
        Args:
            stats: dicionário com estatísticas do número
            
        Returns:
            float: score de probabilidade (quanto maior, mais provável)
        """
        score = 0
        
        # Se está aparecendo, verifica se está dentro da média de sequência presente
        if stats['apareceu_ultimo']:
            if stats['sorteios_aparecendo'] < stats['media_seq_presente']:
                # Ainda está na janela esperada de aparição
                score += 50
            else:
                # Já passou da média, menos provável
                score += 20
        else:
            # Se está ausente, verifica se já passou tempo suficiente
            if stats['sorteios_sem_aparecer'] >= stats['media_seq_ausente']:
                # Já está "devendo" aparecer
                score += 60
            else:
                # Ainda está na janela normal de ausência
                score += 10
        
        # Bônus pela frequência total
        freq_normalizada = stats['total_aparicoes'] / len(self.historico_numeros)
        score += freq_normalizada * 30
        
        # Penalidade se está em sequência muito longa (improvável continuar)
        if stats['apareceu_ultimo'] and stats['sorteios_aparecendo'] > stats['max_seq_presente'] * 0.8:
            score -= 30
        
        return score
    
    def jogo_probabilidade_padrao(self):
        """
        Jogo 3: 15 números com maior probabilidade baseada em padrões.
        
        Returns:
            lista com os 15 números mais prováveis
        """
        probabilidades = []
        
        print("\n=== JOGO 3: ANÁLISE DE PADRÕES ===")
        print("Analisando padrões de cada número...\n")
        
        for numero in self.todos_numeros:
            stats = self._analisar_padroes_numero(numero)
            prob = self.calcular_probabilidade_proximo(stats)
            probabilidades.append((numero, prob, stats))
        
        # Ordena por probabilidade
        probabilidades.sort(key=lambda x: x[1], reverse=True)
        
        # Pega os 15 mais prováveis
        top15 = probabilidades[:15]
        numeros_selecionados = [num for num, _, _ in top15]
        
        print("Top 15 números mais prováveis:\n")
        for num, prob, stats in top15:
            status = "PRESENTE" if stats['apareceu_ultimo'] else "AUSENTE"
            if stats['apareceu_ultimo']:
                detalhe = f"há {stats['sorteios_aparecendo']} sorteio(s)"
            else:
                detalhe = f"há {stats['sorteios_sem_aparecer']} sorteio(s)"
            
            print(f"  Número {num:2d}: Score {prob:5.1f} | {status} {detalhe}")
            print(f"    Média presente: {stats['media_seq_presente']:.1f} | "
                  f"Média ausente: {stats['media_seq_ausente']:.1f}")
        
        print(f"\nNúmeros selecionados: {sorted(numeros_selecionados)}")
        
        return sorted(numeros_selecionados)
    
    def jogo_pares_impares_equilibrado(self):
        """
        Jogo 4: Baseado no equilíbrio entre pares e ímpares.
        Estatisticamente, jogos muito desequilibrados são raros.
        """
        print("\n=== JOGO 4: EQUILÍBRIO PARES/ÍMPARES ===")
        
        # Analisa distribuição histórica de pares/ímpares
        dist_pares = []
        for jogo in self.historico_numeros:
            qtd_pares = sum(1 for n in jogo if n % 2 == 0)
            dist_pares.append(qtd_pares)
        
        # Encontra a distribuição mais comum
        contador_dist = Counter(dist_pares)
        qtd_pares_ideal = contador_dist.most_common(1)[0][0]
        qtd_impares_ideal = 15 - qtd_pares_ideal
        
        print(f"Distribuição mais comum: {qtd_pares_ideal} pares e {qtd_impares_ideal} ímpares")
        print(f"Ocorreu {contador_dist[qtd_pares_ideal]} vezes ({contador_dist[qtd_pares_ideal]/len(self.historico_numeros)*100:.1f}%)")
        
        # Seleciona os números mais frequentes respeitando o equilíbrio
        todos = [num for jogo in self.historico_numeros for num in jogo]
        contador = Counter(todos)
        
        pares = sorted([n for n in self.todos_numeros if n % 2 == 0], 
                      key=lambda x: contador[x], reverse=True)
        impares = sorted([n for n in self.todos_numeros if n % 2 != 0], 
                        key=lambda x: contador[x], reverse=True)
        
        jogo = sorted(pares[:qtd_pares_ideal] + impares[:qtd_impares_ideal])
        
        print(f"\nNúmeros selecionados: {jogo}")
        print(f"Pares: {[n for n in jogo if n % 2 == 0]}")
        print(f"Ímpares: {[n for n in jogo if n % 2 != 0]}")
        
        return jogo
    
    def jogo_sequencias_repeticoes(self):
        """
        Jogo 5: Baseado em números que repetem do último sorteio.
        Analisa quantos números costumam repetir entre sorteios consecutivos.
        """
        print("\n=== JOGO 5: ANÁLISE DE REPETIÇÕES ===")
        
        # Analisa quantos números repetem entre sorteios consecutivos
        repeticoes = []
        for i in range(1, len(self.historico_numeros)):
            jogo_anterior = set(self.historico_numeros[i-1])
            jogo_atual = set(self.historico_numeros[i])
            qtd_repeticoes = len(jogo_anterior & jogo_atual)
            repeticoes.append(qtd_repeticoes)
        
        media_repeticoes = int(np.mean(repeticoes))
        print(f"Média de números que repetem: {media_repeticoes}")
        print(f"Mínimo: {min(repeticoes)} | Máximo: {max(repeticoes)}")
        
        # Pega o último sorteio
        ultimo_jogo = set(self.historico_numeros[-1])
        print(f"\nÚltimo sorteio: {sorted(ultimo_jogo)}")
        
        # Calcula frequência dos números (exceto os do último jogo)
        todos_exceto_ultimo = [num for jogo in self.historico_numeros[:-1] for num in jogo]
        contador = Counter(todos_exceto_ultimo)
        
        # Seleciona números do último jogo (baseado na média de repetições)
        numeros_ultimo_ordenados = sorted(ultimo_jogo, 
                                         key=lambda x: contador[x], 
                                         reverse=True)
        numeros_repetidos = numeros_ultimo_ordenados[:media_repeticoes]
        
        # Completa com números novos (não do último jogo) mais frequentes
        numeros_novos = [n for n in self.todos_numeros if n not in ultimo_jogo]
        numeros_novos_ordenados = sorted(numeros_novos, 
                                        key=lambda x: contador[x], 
                                        reverse=True)
        
        qtd_novos = 15 - len(numeros_repetidos)
        jogo = sorted(numeros_repetidos + numeros_novos_ordenados[:qtd_novos])
        
        print(f"\nRepetidos do último: {sorted(numeros_repetidos)}")
        print(f"Números novos: {sorted(numeros_novos_ordenados[:qtd_novos])}")
        print(f"Jogo completo: {jogo}")
        
        return jogo
    
    def jogo_distribuicao_espacial(self):
        """
        Jogo 6: Baseado na distribuição espacial (faixas de números).
        Divide em 5 faixas (1-5, 6-10, 11-15, 16-20, 21-25).
        """
        print("\n=== JOGO 6: DISTRIBUIÇÃO ESPACIAL ===")
        
        faixas = {
            '01-05': list(range(1, 6)),
            '06-10': list(range(6, 11)),
            '11-15': list(range(11, 16)),
            '16-20': list(range(16, 21)),
            '21-25': list(range(21, 26))
        }
        
        # Analisa quantos números por faixa aparecem em média
        dist_faixas = {f: [] for f in faixas.keys()}
        
        for jogo in self.historico_numeros:
            for nome_faixa, numeros_faixa in faixas.items():
                qtd_na_faixa = sum(1 for n in jogo if n in numeros_faixa)
                dist_faixas[nome_faixa].append(qtd_na_faixa)
        
        # Calcula média por faixa
        print("Distribuição média por faixa:")
        medias_faixa = {}
        for nome_faixa, valores in dist_faixas.items():
            media = int(round(np.mean(valores)))
            medias_faixa[nome_faixa] = media
            print(f"  Faixa {nome_faixa}: {media} números (média: {np.mean(valores):.2f})")
        
        # Seleciona números mais frequentes de cada faixa
        todos = [num for jogo in self.historico_numeros for num in jogo]
        contador = Counter(todos)
        
        jogo = []
        for nome_faixa, numeros_faixa in faixas.items():
            qtd_selecionar = medias_faixa[nome_faixa]
            nums_ordenados = sorted(numeros_faixa, 
                                   key=lambda x: contador[x], 
                                   reverse=True)
            jogo.extend(nums_ordenados[:qtd_selecionar])
        
        jogo = sorted(jogo)
        
        print(f"\nNúmeros selecionados: {jogo}")
        for nome_faixa, numeros_faixa in faixas.items():
            nums_na_faixa = [n for n in jogo if n in numeros_faixa]
            print(f"  Faixa {nome_faixa}: {nums_na_faixa}")
        
        return jogo
    
    def jogo_machine_learning_scoring(self):
        """
        Jogo 7: Sistema de pontuação combinando múltiplos critérios.
        Modelo híbrido que pondera diferentes análises.
        """
        print("\n=== JOGO 7: SCORING MULTIFATORIAL ===")
        
        scores = {n: 0 for n in self.todos_numeros}
        
        # Critério 1: Frequência geral (peso 25%)
        todos = [num for jogo in self.historico_numeros for num in jogo]
        contador = Counter(todos)
        max_freq = max(contador.values())
        for num in self.todos_numeros:
            scores[num] += (contador[num] / max_freq) * 25
        
        # Critério 2: Tendência recente - últimos 50 jogos (peso 30%)
        recentes = [num for jogo in self.historico_numeros[-50:] for num in jogo]
        contador_recente = Counter(recentes)
        max_freq_recente = max(contador_recente.values()) if contador_recente else 1
        for num in self.todos_numeros:
            scores[num] += (contador_recente.get(num, 0) / max_freq_recente) * 30
        
        # Critério 3: Análise de padrão (peso 25%)
        for num in self.todos_numeros:
            stats = self._analisar_padroes_numero(num)
            prob_padrao = self.calcular_probabilidade_proximo(stats)
            scores[num] += (prob_padrao / 100) * 25
        
        # Critério 4: Números "quentes" - apareceram nos últimos 5 sorteios (peso 20%)
        ultimos_5 = [num for jogo in self.historico_numeros[-5:] for num in jogo]
        contador_quentes = Counter(ultimos_5)
        for num in self.todos_numeros:
            if contador_quentes.get(num, 0) >= 2:  # Apareceu 2+ vezes
                scores[num] += 20
            elif contador_quentes.get(num, 0) == 1:
                scores[num] += 10
        
        # Ordena por score
        ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        print("Top 15 números com maior score:\n")
        for i, (num, score) in enumerate(ranking[:15], 1):
            freq_total = contador[num]
            freq_recente = contador_recente.get(num, 0)
            print(f"  {i:2d}. Número {num:2d}: {score:5.1f} pontos "
                  f"(Total: {freq_total}, Recente: {freq_recente})")
        
        jogo = sorted([num for num, _ in ranking[:15]])
        print(f"\nJogo selecionado: {jogo}")
        
        return jogo
    
    def gerar_todos_jogos(self):
        """Gera os 7 jogos e retorna um resumo."""
        print("=" * 60)
        print("ANALISADOR LOTOFÁCIL - VERSÃO COMPLETA")
        print(f"Total de sorteios analisados: {len(self.historico_numeros)}")
        print("=" * 60)
        
        jogo1 = self.jogo_mais_sorteados()
        jogo2 = self.jogo_menos_sorteados()
        jogo3 = self.jogo_probabilidade_padrao()
        jogo4 = self.jogo_pares_impares_equilibrado()
        jogo5 = self.jogo_sequencias_repeticoes()
        jogo6 = self.jogo_distribuicao_espacial()
        jogo7 = self.jogo_machine_learning_scoring()
        
        print("\n" + "=" * 70)
        print("RESUMO DOS JOGOS")
        print("=" * 70)
        print(f"\nJogo 1 (Mais sorteados):        {jogo1}")
        print(f"Jogo 2 (Menos sorteados):       {jogo2}")
        print(f"Jogo 3 (Padrão/Probabilid.):    {jogo3}")
        print(f"Jogo 4 (Equilíbrio Par/Ímpar):  {jogo4}")
        print(f"Jogo 5 (Repetições):            {jogo5}")
        print(f"Jogo 6 (Distribuição Espacial): {jogo6}")
        print(f"Jogo 7 (Scoring Multifatorial): {jogo7}")
        
        return {
            'jogo1_mais_sorteados': jogo1,
            'jogo2_menos_sorteados': jogo2,
            'jogo3_probabilidade': jogo3,
            'jogo4_pares_impares': jogo4,
            'jogo5_repeticoes': jogo5,
            'jogo6_distribuicao': jogo6,
            'jogo7_scoring': jogo7
        }


# EXEMPLO DE USO
if __name__ == "__main__":
    # Substitua pelo caminho do seu arquivo CSV
    arquivo = "historico_lotofacil.csv"
    
    try:
        analisador = AnalisadorLotofacil(arquivo)
        jogos = analisador.gerar_todos_jogos()
        
        # Salvar jogos em arquivo
        with open("jogos_gerados.txt", "w", encoding="utf-8") as f:
            f.write("JOGOS LOTOFÁCIL GERADOS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Jogo 1 (Mais sorteados):          {jogos['jogo1_mais_sorteados']}\n")
            f.write(f"Jogo 2 (Menos sorteados):         {jogos['jogo2_menos_sorteados']}\n")
            f.write(f"Jogo 3 (Padrão/Probabilid.):      {jogos['jogo3_probabilidade']}\n")
            f.write(f"Jogo 4 (Equilíbrio Par/Ímpar):    {jogos['jogo4_pares_impares']}\n")
            f.write(f"Jogo 5 (Repetições):              {jogos['jogo5_repeticoes']}\n")
            f.write(f"Jogo 6 (Distribuição Espacial):   {jogos['jogo6_distribuicao']}\n")
            f.write(f"Jogo 7 (Scoring Multifatorial):   {jogos['jogo7_scoring']}\n")
        
        print("\n✓ Jogos salvos em 'jogos_gerados.txt'")
        
    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo}' não encontrado!")
        print("\nFormato esperado do CSV:")
        print("- Cada linha = um sorteio")
        print("- Colunas com os 15 números sorteados")
        print("- Exemplo: Concurso,Data,Bola1,Bola2,...,Bola15")