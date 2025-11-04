import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock

# Importa a classe que queremos testar
from lotofacil_analyzer import AnalisadorLotofacil, TENSORFLOW_AVAILABLE

# Conteúdo do CSV falso que será usado nos testes.
# Usamos um histórico pequeno e controlado para ter resultados previsíveis.
MOCK_CSV_DATA = """Concurso;Data Sorteio;Bola1;Bola2;Bola3;Bola4;Bola5;Bola6;Bola7;Bola8;Bola9;Bola10;Bola11;Bola12;Bola13;Bola14;Bola15
1;01/01/2023;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15
2;02/01/2023;1;2;3;4;5;16;17;18;19;20;21;22;23;24;25
3;03/01/2023;1;2;3;6;7;8;9;10;11;16;17;18;19;20;25
"""

@pytest.fixture
def analisador_mock(tmp_path: Path) -> AnalisadorLotofacil:
    """
    Fixture do Pytest que cria um ambiente de teste isolado.
    
    1. `tmp_path`: Uma fixture nativa do pytest que cria um diretório temporário.
    2. Cria um arquivo CSV falso dentro desse diretório.
    3. Inicializa a classe AnalisadorLotofacil com o caminho para este arquivo falso.
    4. Retorna a instância do analisador para ser usada nos testes.
    """
    csv_path = tmp_path / "mock_lotofacil.csv"
    csv_path.write_text(MOCK_CSV_DATA, encoding='latin-1')
    
    # Retorna uma instância da classe pronta para o teste
    return AnalisadorLotofacil(str(csv_path))


def test_extracao_historico(analisador_mock: AnalisadorLotofacil):
    """Testa se o histórico foi extraído corretamente do CSV."""
    # Esperamos 3 jogos no nosso histórico mock
    assert len(analisador_mock.historico_numeros) == 3
    
    # Verifica se o primeiro jogo foi lido e ordenado corretamente
    primeiro_jogo_esperado = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    assert analisador_mock.historico_numeros[0] == primeiro_jogo_esperado

    # Verifica o último jogo
    ultimo_jogo_esperado = sorted([1, 2, 3, 6, 7, 8, 9, 10, 11, 16, 17, 18, 19, 20, 25])
    assert analisador_mock.historico_numeros[2] == ultimo_jogo_esperado

def test_jogo_mais_sorteados(analisador_mock: AnalisadorLotofacil):
    """Testa a lógica para encontrar os números mais sorteados."""
    # Com nosso histórico mock, os números 1, 2, 3 aparecem 3 vezes.
    # Outros aparecem 2 vezes. O resto, 1 vez.
    # A função deve retornar os 15 mais frequentes.
    resultado, _ = analisador_mock.jogo_mais_sorteados()
    
    # Os números 1, 2, 3 DEVEM estar na lista
    assert 1 in resultado
    assert 2 in resultado
    assert 3 in resultado
    
    # Os números 13, 14, 21, 22, 23, 24 (que só aparecem 1 vez) NÃO DEVEM estar na lista dos 15 mais.
    # No nosso caso, há mais de 15 números que aparecem 2 ou 3 vezes, então a seleção exata
    # pode depender da ordem interna do Counter. O importante é testar as inclusões/exclusões certas.
    # Vamos verificar os que aparecem 2x: 4, 5, 6, 7, 8, 9, 10, 11, 16, 17, 18, 19, 20, 25
    # Total: 3 (3x) + 14 (2x) = 17 números. Os 15 mais comuns serão os 3 de 3x e 12 dos de 2x.
    # Os números 13, 14, 15, 21, 22, 23, 24 (1x) não devem estar.
    assert 13 not in resultado
    assert 14 not in resultado
    assert 21 not in resultado
    
    assert len(resultado) == 15

def test_jogo_menos_sorteados(analisador_mock: AnalisadorLotofacil):
    """Testa a lógica para encontrar os números menos sorteados."""
    resultado, _ = analisador_mock.jogo_menos_sorteados()
    
    # Números que aparecem apenas 1 vez: 12, 13, 14, 15, 21, 22, 23, 24
    # Todos eles devem estar na lista dos menos sorteados.
    assert 13 in resultado
    assert 14 in resultado
    assert 15 in resultado
    assert 21 in resultado
    assert 22 in resultado
    assert 23 in resultado
    assert 24 in resultado
    
    # Números que aparecem 3 vezes (1, 2, 3) não devem estar na lista dos menos sorteados.
    assert 1 not in resultado
    assert 2 not in resultado
    assert 3 not in resultado
    
    assert len(resultado) == 15

def test_jogo_pares_impares_equilibrado(analisador_mock: AnalisadorLotofacil):
    """Testa a lógica de equilíbrio par/ímpar."""
    # Histórico de pares: Jogo1 (6), Jogo2 (7), Jogo3 (8)
    # A distribuição mais comum de pares é... nenhuma, todas ocorreram 1 vez.
    # O `most_common(1)` pode retornar 6, 7 ou 8. O teste precisa ser flexível
    # ou o método precisa ter um desempate definido.
    # Assumindo que o `Counter` pega o último que viu em caso de empate, seria 8.
    # Qtd Pares Ideal = 8, Qtd Ímpares Ideal = 7
    
    resultado, _ = analisador_mock.jogo_pares_impares_equilibrado()
    
    qtd_pares = sum(1 for n in resultado if n % 2 == 0)
    qtd_impares = sum(1 for n in resultado if n % 2 != 0)
    
    # O resultado deve ter 15 números
    assert len(resultado) == 15
    # A proporção deve ser a mais comum encontrada (ou uma delas, em caso de empate)
    assert (qtd_pares == 8 and qtd_impares == 7) or \
           (qtd_pares == 7 and qtd_impares == 8) or \
           (qtd_pares == 6 and qtd_impares == 9)


def test_analisar_padroes_numero():
    """
    Testa o método privado _analisar_padroes_numero com um histórico customizado.
    Isso garante que a lógica de contagem de sequências está correta.
    """
    # Histórico customizado para o número 5: P, P, A, A, A, P, A
    # P = Presente, A = Ausente
    custom_csv_data = """Concurso;Data Sorteio;Bola1;Bola2;Bola3;Bola4;Bola5;Bola6;Bola7;Bola8;Bola9;Bola10;Bola11;Bola12;Bola13;Bola14;Bola15
1;01/01/2023;1;2;3;4;5;6;7;8;9;10;11;12;13;14;16
2;02/01/2023;1;2;3;4;5;6;7;8;9;10;11;12;13;14;17
3;03/01/2023;1;2;3;4;6;7;8;9;10;11;12;13;14;16;17
4;04/01/2023;1;2;3;4;6;7;8;9;10;11;12;13;14;16;17
5;05/01/2023;1;2;3;4;6;7;8;9;10;11;12;13;14;16;17
6;06/01/2023;1;2;3;4;5;6;7;8;9;10;11;12;13;14;18
7;07/01/2023;1;2;3;4;6;7;8;9;10;11;12;13;14;16;19
"""
    # Usamos um truque com `io.StringIO` para simular um arquivo sem usar o disco
    from io import StringIO
    analisador = AnalisadorLotofacil(StringIO(custom_csv_data))

    # Analisa o padrão do número 5
    stats = analisador._analisar_padroes_numero(5)

    # Verificações com base no padrão P, P, A, A, A, P, A
    assert stats['numero'] == 5
    assert stats['total_aparicoes'] == 3
    assert stats['apareceu_ultimo'] is False
    assert stats['sorteios_sem_aparecer'] == 1
    assert stats['sorteios_aparecendo'] == 0
    
    # Sequências de presença: [2, 1]
    assert stats['max_seq_presente'] == 2
    assert np.isclose(stats['media_seq_presente'], 1.5)
    
    # Sequências de ausência: [3, 1]
    assert stats['max_seq_ausente'] == 3
    assert np.isclose(stats['media_seq_ausente'], 2.0)


def test_jogo_machine_learning_scoring(analisador_mock: AnalisadorLotofacil):
    """
    Testa a lógica de pontuação do jogo de machine learning.
    Verifica se os números mais e menos frequentes recebem scores coerentes.
    """
    resultado, _ = analisador_mock.jogo_machine_learning_scoring()

    # No nosso mock, o número 1 é o mais frequente e sempre presente.
    # Deve estar na lista final.
    assert 1 in resultado

    # O número 13 é um dos menos frequentes e apareceu apenas no primeiro jogo.
    # É muito improvável que ele tenha um score alto.
    assert 13 not in resultado

    # O resultado deve sempre conter 15 números únicos.
    assert len(resultado) == 15
    assert len(set(resultado)) == 15


def test_jogo_clusterizacao_kmeans(analisador_mock: AnalisadorLotofacil):
    """
    Testa a lógica de clusterização com K-Means.
    Como o random_state está fixo, o resultado é determinístico.
    """
    # Modificamos o método diretamente na instância do mock para usar
    # um número de clusters menor que o número de amostras (3).
    # Isso evita o erro do K-Means e permite testar a lógica principal.
    from functools import partial
    analisador_mock.jogo_clusterizacao_kmeans = partial(
        analisador_mock.jogo_clusterizacao_kmeans, n_clusters_override=2
    )
    resultado, detalhes = analisador_mock.jogo_clusterizacao_kmeans()

    # 1. Verifica a estrutura do retorno
    assert isinstance(resultado, list)
    assert isinstance(detalhes, list)

    # 2. Verifica se o jogo gerado tem o tamanho correto
    assert len(resultado) == 15
    assert len(set(resultado)) == 15

    # 3. Verifica se os números mais comuns do mock (1, 2, 3) estão no resultado,
    #    pois eles influenciam fortemente os centróides.
    assert 1 in resultado
    assert 2 in resultado
    assert 3 in resultado


@pytest.mark.skipif(not TENSORFLOW_AVAILABLE, reason="TensorFlow não está instalado")
def test_jogo_series_temporais_lstm_sucesso(analisador_mock: AnalisadorLotofacil, monkeypatch):
    """
    Testa o caminho de sucesso do modelo LSTM, zombando (mocking) do treinamento e da previsão.
    Isso torna o teste rápido e determinístico.
    """
    # 1. Criar um histórico longo o suficiente para o LSTM
    # A função requer `sequence_length + 1` (10 + 1 = 11) jogos.
    analisador_mock.historico_numeros = [
        list(range(i, i + 15)) for i in range(1, 12)
    ]

    # 2. Mockar o modelo Keras para evitar o treinamento real
    mock_model = MagicMock()
    # O método predict deve retornar um array de 25 probabilidades
    mock_predict_result = np.linspace(1, 0, 25) # Cria um array [1.0, 0.96, ..., 0.0]
    mock_model.predict.return_value = np.array([mock_predict_result])

    # Mockar a classe Sequential para que ela retorne nosso mock_model
    mock_sequential = MagicMock(return_value=mock_model)
    monkeypatch.setattr('lotofacil_analyzer.Sequential', mock_sequential)

    # 3. Executar a função
    resultado, detalhes = analisador_mock.jogo_series_temporais_lstm()

    # 4. Verificar os resultados
    assert len(resultado) == 15
    assert len(set(resultado)) == 15
    # Com nosso resultado de previsão mockado, os números de 1 a 15 devem ser selecionados
    assert resultado == list(range(1, 16))
    assert "Treinamento concluído." in detalhes
    # Verifica se o modelo foi compilado e treinado (mesmo que de forma mockada)
    mock_model.compile.assert_called_once()
    mock_model.fit.assert_called_once()
    mock_model.predict.assert_called_once()


def test_jogo_series_temporais_lstm_historia_insuficiente(analisador_mock: AnalisadorLotofacil):
    """Testa o comportamento do LSTM quando o histórico é muito curto."""
    # O mock padrão tem apenas 3 jogos, e o LSTM precisa de 11.
    resultado, detalhes = analisador_mock.jogo_series_temporais_lstm()
    if TENSORFLOW_AVAILABLE:
        assert resultado == []
        assert "Histórico insuficiente." in detalhes[0]
    else:
        assert "TensorFlow não está instalado." in detalhes[0]


@pytest.fixture
def analisador_csv_malformado(tmp_path: Path) -> AnalisadorLotofacil:
    """Fixture que cria um CSV com dados inválidos (letras)."""
    malformed_csv_data = """Concurso;Data Sorteio;Bola1;Bola2;Bola3;Bola4;Bola5;Bola6;Bola7;Bola8;Bola9;Bola10;Bola11;Bola12;Bola13;Bola14;Bola15
1;01/01/2023;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15
2;02/01/2023;1;2;3;4;5;16;17;DEZESSETE;19;20;21;22;23;24;25
3;03/01/2023;1;2;3;6;7;8;9;10;11;16;17;18;19;20;25
"""
    csv_path = tmp_path / "malformed_lotofacil.csv"
    csv_path.write_text(malformed_csv_data, encoding='latin-1')
    return AnalisadorLotofacil(str(csv_path))


def test_resiliencia_csv_malformado(analisador_csv_malformado: AnalisadorLotofacil):
    """
    Testa se a classe consegue lidar com linhas malformadas no CSV.
    O método _extrair_historico deve ignorar a linha com erro e continuar.
    """
    # O CSV tem 3 linhas, mas uma é inválida ("DEZESSETE").
    # O histórico extraído deve conter apenas 2 jogos válidos.
    assert len(analisador_csv_malformado.historico_numeros) == 2

    # Verifica se os jogos válidos foram carregados corretamente
    primeiro_jogo_esperado = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    segundo_jogo_valido_esperado = sorted([1, 2, 3, 6, 7, 8, 9, 10, 11, 16, 17, 18, 19, 20, 25])

    assert analisador_csv_malformado.historico_numeros[0] == primeiro_jogo_esperado
    assert analisador_csv_malformado.historico_numeros[1] == segundo_jogo_valido_esperado