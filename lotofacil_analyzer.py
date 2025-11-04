import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime
from sklearn.cluster import KMeans
import os

# Tenta importar o TensorFlow. Se não estiver disponível, o modelo LSTM será desativado.
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

def converter_xlsx_para_csv(arquivo_xlsx, arquivo_csv_saida=None):
    """
    Converte arquivo XLSX para CSV com separador ponto e vírgula.
    
    Args:
        arquivo_xlsx: Caminho do arquivo Excel (.xlsx)
        arquivo_csv_saida: Nome do arquivo CSV de saída (opcional)
                          Se não informado, usa o mesmo nome com extensão .csv
    
    Returns:
        str: Caminho do arquivo CSV gerado
    """
    print(f"🔄 Convertendo {arquivo_xlsx} para CSV...")
    
    # Define nome do arquivo de saída
    if arquivo_csv_saida is None:
        arquivo_csv_saida = arquivo_xlsx.rsplit('.', 1)[0] + '.csv'
    
    try:
        # Lê o arquivo Excel
        df = pd.read_excel(arquivo_xlsx)
        
        # Salva como CSV com separador ponto e vírgula
        df.to_csv(arquivo_csv_saida, sep=';', index=False, encoding='latin-1')
        
        print(f"✅ Arquivo convertido com sucesso: {arquivo_csv_saida}")
        print(f"   Total de linhas: {len(df)}")
        print(f"   Total de colunas: {len(df.columns)}")
        
        return arquivo_csv_saida
        
    except Exception as e:
        print(f"❌ Erro ao converter arquivo: {e}")
        raise

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
    
    def _imprimir_jogo(self, titulo, jogo, detalhes=None):
        """Método auxiliar para imprimir um jogo de forma padronizada."""
        print(f"\n=== {titulo.upper()} ===")
        if detalhes:
            for detalhe in detalhes:
                print(detalhe)
        print(f"Números selecionados: {jogo}")
    
    def jogo_mais_sorteados(self):
        """
        Jogo 1: 15 números mais sorteados no histórico.
        
        Returns:
            tuple: (lista com os 15 números mais frequentes, lista de detalhes para impressão)
        """
        todos = [num for jogo in self.historico_numeros for num in jogo]
        contador = Counter(todos)
        mais_sorteados = [num for num, _ in contador.most_common(15)]
        detalhes = [f"  Número {num:2d}: {contador[num]:4d} vezes" for num in sorted(mais_sorteados)]
        return sorted(mais_sorteados), detalhes
    
    def jogo_menos_sorteados(self):
        """
        Jogo 2: 15 números menos sorteados no histórico.
        
        Returns:
            lista com os 15 números menos frequentes
        """
        todos = [num for jogo in self.historico_numeros for num in jogo]
        contador = Counter(todos)
        menos_sorteados = [num for num, _ in contador.most_common()[-15:]]
        detalhes = [f"  Número {num:2d}: {contador[num]:4d} vezes" for num in sorted(menos_sorteados)]
        return sorted(menos_sorteados), detalhes
    
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

        for numero in self.todos_numeros:
            stats = self._analisar_padroes_numero(numero)
            prob = self.calcular_probabilidade_proximo(stats)
            probabilidades.append((numero, prob, stats))
        
        # Ordena por probabilidade
        probabilidades.sort(key=lambda x: x[1], reverse=True)
        
        # Pega os 15 mais prováveis
        top15 = probabilidades[:15]
        numeros_selecionados = [num for num, _, _ in top15]

        detalhes = ["Analisando padrões de cada número...", "Top 15 números mais prováveis:"]
        for num, prob, stats in top15:
            status = "PRESENTE" if stats['apareceu_ultimo'] else "AUSENTE"
            if stats['apareceu_ultimo']:
                detalhe = f"há {stats['sorteios_aparecendo']} sorteio(s)"
            else:
                detalhe = f"há {stats['sorteios_sem_aparecer']} sorteio(s)"
            detalhes.append(f"  Número {num:2d}: Score {prob:5.1f} | {status} {detalhe}")
            detalhes.append(f"    Média presente: {stats['media_seq_presente']:.1f} | Média ausente: {stats['media_seq_ausente']:.1f}")

        return sorted(numeros_selecionados), detalhes
    
    def jogo_pares_impares_equilibrado(self):
        """
        Jogo 4: Baseado no equilíbrio entre pares e ímpares.
        Estatisticamente, jogos muito desequilibrados são raros.
        """
        # Analisa distribuição histórica de pares/ímpares
        dist_pares = []
        for jogo in self.historico_numeros:
            qtd_pares = sum(1 for n in jogo if n % 2 == 0)
            dist_pares.append(qtd_pares)
        
        # Encontra a distribuição mais comum
        contador_dist = Counter(dist_pares)
        qtd_pares_ideal = contador_dist.most_common(1)[0][0]
        qtd_impares_ideal = 15 - qtd_pares_ideal
        
        # Seleciona os números mais frequentes respeitando o equilíbrio
        todos = [num for jogo in self.historico_numeros for num in jogo]
        contador = Counter(todos)
        
        pares = sorted([n for n in self.todos_numeros if n % 2 == 0], 
                      key=lambda x: contador[x], reverse=True)
        impares = sorted([n for n in self.todos_numeros if n % 2 != 0], 
                        key=lambda x: contador[x], reverse=True)
        
        jogo = sorted(pares[:qtd_pares_ideal] + impares[:qtd_impares_ideal])
        
        detalhes = [
            f"Distribuição mais comum: {qtd_pares_ideal} pares e {qtd_impares_ideal} ímpares",
            f"Ocorreu {contador_dist[qtd_pares_ideal]} vezes ({contador_dist[qtd_pares_ideal]/len(self.historico_numeros)*100:.1f}%)",
            f"Pares selecionados: {[n for n in jogo if n % 2 == 0]}",
            f"Ímpares selecionados: {[n for n in jogo if n % 2 != 0]}"
        ]
        return jogo, detalhes
    
    def jogo_sequencias_repeticoes(self):
        """
        Jogo 5: Baseado em números que repetem do último sorteio.
        Analisa quantos números costumam repetir entre sorteios consecutivos.
        """
        # Analisa quantos números repetem entre sorteios consecutivos
        repeticoes = []
        for i in range(1, len(self.historico_numeros)):
            jogo_anterior = set(self.historico_numeros[i-1])
            jogo_atual = set(self.historico_numeros[i])
            qtd_repeticoes = len(jogo_anterior & jogo_atual)
            repeticoes.append(qtd_repeticoes)
        
        media_repeticoes = int(np.mean(repeticoes))
        
        # Pega o último sorteio
        ultimo_jogo = set(self.historico_numeros[-1])
        
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
        
        detalhes = [
            f"Média de números que repetem: {media_repeticoes} (Min: {min(repeticoes)}, Max: {max(repeticoes)})",
            f"Último sorteio: {sorted(ultimo_jogo)}",
            f"Repetidos do último: {sorted(numeros_repetidos)}",
            f"Números novos: {sorted(numeros_novos_ordenados[:qtd_novos])}"
        ]
        return jogo, detalhes
    
    def jogo_distribuicao_espacial(self):
        """
        Jogo 6: Baseado na distribuição espacial (faixas de números).
        Divide em 5 faixas (1-5, 6-10, 11-15, 16-20, 21-25).
        """
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
        medias_faixa = {}
        detalhes_faixas = ["Distribuição média por faixa:"]
        for nome_faixa, valores in dist_faixas.items():
            media = int(round(np.mean(valores)))
            medias_faixa[nome_faixa] = media
            detalhes_faixas.append(f"  Faixa {nome_faixa}: {media} números (média: {np.mean(valores):.2f})")
        
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
        
        for nome_faixa, numeros_faixa in faixas.items():
            nums_na_faixa = [n for n in jogo if n in numeros_faixa]
            detalhes_faixas.append(f"  Faixa {nome_faixa}: {nums_na_faixa}")
        
        return jogo, detalhes_faixas
    
    def jogo_machine_learning_scoring(self):
        """
        Jogo 7: Sistema de pontuação combinando múltiplos critérios.
        Modelo híbrido que pondera diferentes análises.
        """
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
        
        detalhes = ["Top 15 números com maior score:"]
        for i, (num, score) in enumerate(ranking[:15], 1):
            freq_total = contador[num]
            freq_recente = contador_recente.get(num, 0)
            detalhes.append(f"  {i:2d}. Número {num:2d}: {score:5.1f} pontos "
                            f"(Total: {freq_total}, Recente: {freq_recente})")
        
        jogo = sorted([num for num, _ in ranking[:15]])
        return jogo, detalhes
    
    def jogo_clusterizacao_kmeans(self, n_clusters_override=None):
        """
        Jogo 8: Clusterização (Agrupamento) de Jogos usando K-Means.
        Agrupa jogos históricos em clusters e sugere um jogo baseado no centróide
        do cluster mais representativo (o maior cluster).
        """
        detalhes = ["Analisando padrões de agrupamento de jogos com K-Means..."]
        
        if not self.historico_numeros:
            detalhes.append("Histórico de jogos vazio para clusterização.")
            return [], detalhes

        # 1. Vetorização dos Jogos: Converter cada sorteio em um vetor binário de 25 posições.
        #    Ex: [1, 2, 3, ..., 15] -> [1, 1, 1, 0, 0, ..., 1, 0, 0]
        dados_para_kmeans = np.zeros((len(self.historico_numeros), 25))
        for i, jogo in enumerate(self.historico_numeros):
            for numero in jogo:
                dados_para_kmeans[i, numero - 1] = 1 # -1 porque os números são de 1 a 25, índices de 0 a 24

        # 2. Aplicar K-Means
        #    Escolhemos um número razoável de clusters (K).
        #    Em um cenário real, você poderia usar o método do cotovelo ou silhouette score
        #    para encontrar o K ideal. Para este exemplo, K=5.
        n_clusters = n_clusters_override if n_clusters_override is not None else 5
        try:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10) # n_init para evitar warnings
            kmeans.fit(dados_para_kmeans)
            
            # 3. Análise dos Clusters: Encontrar o maior cluster
            cluster_labels = kmeans.labels_
            cluster_counts = Counter(cluster_labels)
            
            # Encontrar o cluster com mais jogos
            maior_cluster_id = cluster_counts.most_common(1)[0][0]
            detalhes.append(f"Identificados {n_clusters} clusters. O maior cluster é o {maior_cluster_id} com {cluster_counts[maior_cluster_id]} jogos.")
            
            # 4. Obter o centróide do maior cluster
            #    O centróide representa o "jogo médio" daquele cluster.
            centroid_maior_cluster = kmeans.cluster_centers_[maior_cluster_id]
            
            # 5. Selecionar os 15 números com maior "probabilidade" (valor no centróide)
            #    Os valores do centróide são floats entre 0 e 1, representando a frequência média
            #    de cada número naquele cluster.
            numeros_com_prob = [(i + 1, prob) for i, prob in enumerate(centroid_maior_cluster)]
            numeros_com_prob.sort(key=lambda x: x[1], reverse=True)
            
            jogo_sugerido = sorted([num for num, _ in numeros_com_prob[:15]])
            detalhes.append(f"Centróide do maior cluster: {['{:.2f}'.format(p) for p in centroid_maior_cluster]}")
            detalhes.append(f"Top 15 números do centróide: {jogo_sugerido}")
            
            return jogo_sugerido, detalhes
            
        except Exception as e:
            detalhes.append(f"❌ Erro ao executar K-Means: {e}")
            return [], detalhes

    def jogo_series_temporais_lstm(self):
        """
        Jogo 9: Previsão com Rede Neural LSTM (Long Short-Term Memory).
        """
        if not TENSORFLOW_AVAILABLE:
            return [], ["TensorFlow não está instalado. Modelo LSTM desativado.", "Execute: pip install tensorflow"]

        detalhes = ["Analisando o histórico com Rede Neural LSTM..."]
        sequence_length = 10  # Usar 10 sorteios para prever o próximo

        if len(self.historico_numeros) < sequence_length + 1:
            return [], [f"Histórico insuficiente. São necessários pelo menos {sequence_length + 1} sorteios."]

        # 1. Pré-processamento: Vetorização e criação de sequências
        # Converte cada jogo para um vetor binário de 25 posições
        dados_vetorizados = np.array([
            np.isin(self.todos_numeros, jogo).astype(int) for jogo in self.historico_numeros
        ])

        X, y = [], []
        for i in range(len(dados_vetorizados) - sequence_length):
            X.append(dados_vetorizados[i:(i + sequence_length)])
            y.append(dados_vetorizados[i + sequence_length])
        
        X, y = np.array(X), np.array(y)

        # 2. Construção do Modelo LSTM
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(sequence_length, 25)),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(25, activation='sigmoid') # Camada de saída com 25 neurônios e ativação sigmoid
        ])

        # 3. Compilação do Modelo
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        detalhes.append(f"Modelo LSTM criado. Treinando com {len(X)} amostras...")

        # 4. Treinamento
        # Para um resultado real, aumente as épocas e use um conjunto de validação.
        # Aqui, treinamos de forma simples para demonstração.
        try:
            model.fit(X, y, epochs=20, batch_size=32, verbose=0) # verbose=0 para não poluir a saída
            detalhes.append("Treinamento concluído.")
        except Exception as e:
            return [], [f"Erro durante o treinamento do modelo: {e}"]

        # 5. Previsão
        # Pega a última sequência do histórico para prever o próximo jogo
        ultima_sequencia = np.array([dados_vetorizados[-sequence_length:]])
        previsao_prob = model.predict(ultima_sequencia)[0]

        # 6. Geração do Jogo
        # Associa cada probabilidade ao seu número correspondente
        numeros_com_prob = sorted(zip(self.todos_numeros, previsao_prob), key=lambda item: item[1], reverse=True)
        
        jogo_sugerido = sorted([num for num, prob in numeros_com_prob[:15]])
        
        detalhes.append("\nTop 15 números previstos pela LSTM (com probabilidade):")
        for num, prob in numeros_com_prob[:15]:
            detalhes.append(f"  Número {num:2d}: {prob*100:.2f}%")

        return jogo_sugerido, detalhes

    def gerar_todos_jogos(self):
        """Gera todos os jogos e retorna um resumo."""
        print("=" * 60)
        print("ANALISADOR LOTOFÁCIL - VERSÃO COMPLETA")
        print(f"Total de sorteios analisados: {len(self.historico_numeros)}")
        print("=" * 60)
        
        # Dicionário para armazenar os jogos e seus detalhes
        jogos_com_detalhes = {}
        
        jogos_com_detalhes['jogo1_mais_sorteados'] = self.jogo_mais_sorteados()
        jogos_com_detalhes['jogo2_menos_sorteados'] = self.jogo_menos_sorteados()
        jogos_com_detalhes['jogo3_probabilidade'] = self.jogo_probabilidade_padrao()
        jogos_com_detalhes['jogo4_pares_impares'] = self.jogo_pares_impares_equilibrado()
        jogos_com_detalhes['jogo5_repeticoes'] = self.jogo_sequencias_repeticoes()
        jogos_com_detalhes['jogo6_distribuicao'] = self.jogo_distribuicao_espacial()
        jogos_com_detalhes['jogo7_scoring'] = self.jogo_machine_learning_scoring()
        jogos_com_detalhes['jogo8_clusterizacao_kmeans'] = self.jogo_clusterizacao_kmeans()
        jogos_com_detalhes['jogo9_series_temporais_lstm'] = self.jogo_series_temporais_lstm()

        # Imprime os resultados de forma organizada
        jogos_finais = {} # Dicionário para o resumo final (apenas os números)
        for i, (nome_chave, (jogo_numeros, jogo_detalhes)) in enumerate(jogos_com_detalhes.items(), 1):
            # Extrai um título mais legível da chave (ex: 'jogo1_mais_sorteados' -> 'Mais Sorteados')
            partes_nome = nome_chave.split('_')
            titulo_display = " ".join(partes_nome[1:]).replace('-', ' ').title()
            
            self._imprimir_jogo(f"JOGO {i}: {titulo_display}", jogo_numeros, jogo_detalhes)
            jogos_finais[nome_chave] = jogo_numeros # Armazena apenas os números para o resumo
        
        print("\n" + "=" * 70)
        print("RESUMO DOS JOGOS")
        print("=" * 70)
        for nome_chave, jogo_numeros in jogos_finais.items():
            partes_nome = nome_chave.split('_')
            # Formata o título para o resumo (ex: "Jogo 1 (Mais Sorteados)")
            titulo_resumo = " ".join(partes_nome[1:]).replace('-', ' ').title()
            print(f"Jogo {partes_nome[0][4:]} ({titulo_resumo}): {jogo_numeros}")
        
        return jogos_finais       

# EXEMPLO DE USO
if __name__ == "__main__":
    # Substitua pelo caminho do seu arquivo XLSX ou CSV
    arquivo_entrada = "historico_lotofacil.xlsx"  # ou "historico_lotofacil.csv"
    
    try:
        # Verifica se é XLSX e converte automaticamente
        if arquivo_entrada.lower().endswith('.xlsx'):
            print("📁 Arquivo Excel detectado!")
            arquivo_csv = converter_xlsx_para_csv(arquivo_entrada)
            print()
        elif arquivo_entrada.lower().endswith('.csv'):
            print("📁 Arquivo CSV detectado!")
            arquivo_csv = arquivo_entrada
        else:
            print("❌ Formato não suportado! Use .xlsx ou .csv")
            exit(1)
        
        # Analisa os dados
        analisador = AnalisadorLotofacil(arquivo_csv)
        jogos_gerados = analisador.gerar_todos_jogos()
        
        # Salvar jogos em arquivo
        with open("jogos_gerados.txt", "w", encoding="utf-8") as f:
            f.write("JOGOS LOTOFÁCIL GERADOS\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Jogo 1 (Mais sorteados):        {jogos_gerados['jogo1_mais_sorteados']}\n")
            f.write(f"Jogo 2 (Menos sorteados):       {jogos_gerados['jogo2_menos_sorteados']}\n")
            f.write(f"Jogo 3 (Padrão/Probabilid.):    {jogos_gerados['jogo3_probabilidade']}\n")
            f.write(f"Jogo 4 (Equilíbrio Par/Ímpar):  {jogos_gerados['jogo4_pares_impares']}\n")
            f.write(f"Jogo 5 (Repetições):            {jogos_gerados['jogo5_repeticoes']}\n")
            f.write(f"Jogo 6 (Distribuição Espacial): {jogos_gerados['jogo6_distribuicao']}\n")
            f.write(f"Jogo 7 (Scoring Multifatorial): {jogos_gerados['jogo7_scoring']}\n")
            f.write(f"Jogo 8 (Clusterizacao Kmeans):  {jogos_gerados['jogo8_clusterizacao_kmeans']}\n")
            f.write(f"Jogo 9 (Series Temporais Lstm): {jogos_gerados['jogo9_series_temporais_lstm']}\n")
        
        print("\n✅ Jogos gerados e salvos em 'jogos_gerados.txt'")
        
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo '{arquivo_entrada}' não encontrado!")
        print("\nFormatos aceitos:")
        print("  • Excel (.xlsx)")
        print("  • CSV com separador ';' (.csv)")
    except Exception as e:
        print(f"❌ Erro ao processar: {e}")