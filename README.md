
# Otimizador de Cortes CNC

Este repositório contém uma proposta de solução para uma atividade de Inteligência Artificial do curso de Sistemas de Informação. O objetivo é otimizar os pontos de corte de uma barra CNC com dimensões 200 x 100, distribuindo os recortes disponíveis de forma a minimizar desperdícios e evitar sobreposições.

## Problema

Dada uma chapa de 200 (largura) x 100 (altura) e um conjunto de peças (recortes) definidos conforme abaixo:

```python
recortes_disponiveis = [
    {"tipo": "retangular", "largura": 29, "altura": 29, "x": 1, "y": 1, "rotacao": 0},
    {"tipo": "retangular", "largura": 29, "altura": 29, "x": 31, "y": 1, "rotacao": 0},
    {"tipo": "retangular", "largura": 29, "altura": 29, "x": 1, "y": 31, "rotacao": 0},
    {"tipo": "retangular", "largura": 29, "altura": 29, "x": 1, "y": 69, "rotacao": 0},
    {"tipo": "retangular", "largura": 139, "altura": 29, "x": 60, "y": 70, "rotacao": 0},
    {"tipo": "retangular", "largura": 60, "altura": 8, "x": 66, "y": 52, "rotacao": 0},
    {"tipo": "retangular", "largura": 44, "altura": 4, "x": 117, "y": 39, "rotacao": 0},
    {"tipo": "diamante", "largura": 29, "altura": 48, "x": 32, "y": 31, "rotacao": 0},
    {"tipo": "diamante", "largura": 29, "altura": 48, "x": 62, "y": 2, "rotacao": 0},
    {"tipo": "diamante", "largura": 29, "altura": 48, "x": 94, "y": 2, "rotacao": 0},
    {"tipo": "circular", "r": 16, "x": 124, "y": 2},
    {"tipo": "circular", "r": 16, "x": 158, "y": 2}
]
```

O desafio é encontrar a melhor disposição (layout) que permita cortar essas peças da chapa, maximizando o aproveitamento da área e garantindo que os recortes não se sobreponham nem ultrapassem os limites da chapa.

## Proposta de Solução

A solução proposta utiliza uma abordagem híbrida baseada em heurísticas para gerar layouts válidos. O algoritmo central é o **FlexiblePacking**, que aplica diferentes estratégias de varredura (por exemplo: da esquerda para a direita com varredura de cima para baixo, ou inversamente) para posicionar os recortes na chapa. Essa classe foi integrada em duas propostas de solução:

1. **Algoritmo Genético (genetic_algorithm.py):**  
   Utiliza o FlexiblePacking para gerar indivíduos (layouts) válidos, que são evoluídos ao longo de várias gerações por meio de operadores genéticos (seleção, cruzamento, mutação e elitismo).

2. **Ant Colony Optimization (ant_colony.py):**  
   Inspira-se no comportamento de formigas, utilizando feromônios para guiar as decisões (como a configuração de varredura, ordem dos recortes, rotação e priorização horizontal/vertical) e construir soluções. Cada formiga constrói um layout usando o FlexiblePacking e os feromônios são atualizados com base na qualidade das soluções.

Ambos os métodos usam a classe **PackingBase** para centralizar funções comuns (como o cálculo de área, determinação do bounding box, rotação de vértices, etc.), mantendo o código modular e facilitando a manutenção.

### Especificações da Solução:

A solução coloca uma margem de 1 pixel entre os elementos, garantindo espaço suficiente para evitar sobreposição ou erros mecânicos no corte.
- Retângulos: São rotacionados apenas em 0º ou 90º.
- Diamantes: Podem ser rotacionados de 0º a 90º em incrementos de 10º.
- Círculos: Não são rotacionados, pois sua forma é simétrica.

## Requisitos

- **Python 3.6+** (por causa das f-strings)
- **Numpy**
- **Math** (biblioteca padrão do Python)
- **common.layout_display** (para exibição dos layouts)  
- **common.packing_base** (contendo a classe PackingBase)

Certifique-se de que todas as dependências estejam instaladas. Você pode instalar as dependências com pip, se necessário.

## Como Rodar o Projeto

1. Clone o repositório:

   ```bash
   git clone <URL-do-repositório>
   cd <nome-da-pasta-do-repositório>
   ```

2. Para rodar o projeto:

   - Descomente qual algoritmo evolutivo deseja usar
   - Execute o comando:


   ```bash
   python app.py
   ```

Cada execução exibirá o layout inicial e o layout otimizado utilizando o método de exibição presente no `LayoutDisplayMixin`.

## Comentários

**Desempenho dos Algoritmos:**
- Observou-se que o algoritmo de Ant Colony Optimization (ACO) tende a demorar mais que o Algoritmo Genético (AG). Isso ocorre porque o ACO cria uma quantidade maior de soluções (indivíduos) durante cada iteração, utilizando o heurístico para construir layouts de forma mais detalhada. Em contrapartida, o AG utiliza o heurístico apenas na geração da população inicial e, a partir daí, evolui as soluções por meio de operadores genéticos, o que resulta em um processamento mais rápido.

**Resultados Visuais:**
- Layout otimizado em uma execução usando AG:
  ![image](https://github.com/user-attachments/assets/edb158aa-425c-4a7b-b392-3d42694c7735)

- Layout otimizado em uma execução usando ACO:
  ![AntColony](https://github.com/user-attachments/assets/fdaa35cb-3342-49df-a5f0-90ae03f8b787)

