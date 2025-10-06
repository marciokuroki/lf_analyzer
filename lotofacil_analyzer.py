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
        
        # Verifica situação atual (últimos sorteios)
        sorteios_sem_aparecer = 0
        sorteios_aparecendo = 0
        
        for i in range(len(aparicoes) - 1, -1, -1):
            if aparicoes[i] == 0:
                sorteios_sem_aparecer += 1
                if sorteios_aparecendo > 0:
                    break
            else:
                sorteios_aparecendo += 1
                if sorteios_sem_aparecer > 0:
                    break
        
        return {
            'numero': numero,
            'total_aparicoes': sum(aparicoes),
            'media_seq_presente': np.mean(sequencias_presente) if sequencias_presente else 0,
            'media_seq_ausente': np.mean(sequencias_ausente) if sequencias_ausente else 0,
            'max_seq_presente': max(sequencias_presente) if sequencias_presente else 0,
            'max_seq_ausente': max(sequencias_ausente) if sequencias_ausente else 0,
            'sorteios_sem_aparecer': sorteios_sem_aparecer,
            'sorteios_aparecendo': sorteios_aparecendo,
            'apareceu_ultimo': aparicoes[-1] == 1
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
    
    def gerar_todos_jogos(self):
        """Gera os 3 jogos e retorna um resumo."""
        print("=" * 60)
        print("ANALISADOR LOTOFÁCIL")
        print(f"Total de sorteios analisados: {len(self.historico_numeros)}")
        print("=" * 60)
        
        jogo1 = self.jogo_mais_sorteados()
        jogo2 = self.jogo_menos_sorteados()
        jogo3 = self.jogo_probabilidade_padrao()
        
        print("\n" + "=" * 60)
        print("RESUMO DOS JOGOS")
        print("=" * 60)
        print(f"\nJogo 1 (Mais sorteados):     {jogo1}")
        print(f"Jogo 2 (Menos sorteados):    {jogo2}")
        print(f"Jogo 3 (Padrão/Probabilid.): {jogo3}")
        
        return {
            'jogo1_mais_sorteados': jogo1,
            'jogo2_menos_sorteados': jogo2,
            'jogo3_probabilidade': jogo3
        }


# EXEMPLO DE USO
if __name__ == "__main__":
    # Substitua pelo caminho do seu arquivo CSV
    arquivo = "lotofacil20251006.csv"
    
    try:
        analisador = AnalisadorLotofacil(arquivo)
        jogos = analisador.gerar_todos_jogos()
        
        # Salvar jogos em arquivo
        with open("jogos_gerados.txt", "w", encoding="utf-8") as f:
            f.write("JOGOS LOTOFÁCIL GERADOS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Jogo 1 (Mais sorteados):     {jogos['jogo1_mais_sorteados']}\n")
            f.write(f"Jogo 2 (Menos sorteados):    {jogos['jogo2_menos_sorteados']}\n")
            f.write(f"Jogo 3 (Padrão/Probabilid.): {jogos['jogo3_probabilidade']}\n")
        
        print("\n✓ Jogos salvos em 'jogos_gerados.txt'")
        
    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo}' não encontrado!")
        print("\nFormato esperado do CSV:")
        print("- Cada linha = um sorteio")
        print("- Colunas com os 15 números sorteados")
        print("- Exemplo: Concurso,Data,Bola1,Bola2,...,Bola15")