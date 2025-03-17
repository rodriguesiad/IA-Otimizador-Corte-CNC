
# **Otimizador de Cortes CNC utilizando Ant Colony Optimization (ACO)**  

Este repositório apresenta uma solução para a atividade de Inteligência Artificial do curso de graduação em Sistemas de Informação, focada na otimização de cortes em chapas metálicas por meio de Algoritmos Evolutivos. O objetivo é organizar os recortes de forma a maximizar o aproveitamento da chapa CNC, reduzindo desperdícios e garantindo que as peças não se sobreponham nem ultrapassem os limites da chapa

---

## **Problema**  

Dada uma chapa de **200 (largura) x 100 (altura)** e um conjunto de peças (recortes) definidos conforme abaixo:  

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
 ![INICIAL](https://github.com/user-attachments/assets/d5c61c37-4894-4ad5-a902-802db0e4564f)

O desafio consiste em encontrar a **melhor disposição (layout)** para esses recortes, garantindo um **uso eficiente da matéria-prima** e minimizando espaços vazios.  

---

## **Proposta de Solução**  

A solução utiliza o **Algoritmo de Otimização por Colônia de Formigas (ACO)**, que se inspira no comportamento de formigas para encontrar caminhos eficientes. Cada formiga gera uma solução viável de disposição dos recortes, guiando-se por feromônios artificiais que reforçam boas soluções ao longo das iterações.  

A otimização ocorre através das seguintes estratégias:  

- **Configuração da varredura:** Diferentes padrões de leitura da chapa são testados (exemplo: da esquerda para a direita, de baixo para cima, etc.).  
- **Ordenação dos recortes:** A ordem das peças influencia no aproveitamento do espaço e é ajustada ao longo das iterações.  
- **Rotação das peças:** Peças retangulares podem ser giradas 0° ou 90°, enquanto peças diamante podem ter rotações de 0° a 90° em incrementos de 10°.  
- **Priorização horizontal/vertical:** Algumas execuções priorizam preenchimento horizontal antes do vertical e vice-versa, dependendo da heurística de feromônios.  

A cada iteração, as soluções melhor avaliadas reforçam suas escolhas, permitindo que o algoritmo encontre um **layout otimizado** para a chapa.  

---

## **FlexiblePacking: Heurística de Posicionamento de Recortes**  

O **FlexiblePacking** é um módulo essencial que trabalha em conjunto com o **ACO** para garantir que os recortes sejam alocados corretamente na chapa. Ele implementa uma **heurística de empacotamento**, ou seja, um conjunto de regras para posicionar as peças respeitando as restrições do problema.  

### **Funcionalidade Principal**  
O **FlexiblePacking** recebe uma chapa e uma lista de recortes disponíveis e tenta alocar essas peças da forma mais eficiente possível, evitando sobreposições e respeitando os limites da chapa.  

### **Características do FlexiblePacking:**  
✅ **Ordem de varredura dinâmica:** Define a forma como os recortes são alocados na chapa, podendo ser da esquerda para a direita, de cima para baixo, entre outras variações.  
✅ **Margem de segurança:** Adiciona um pequeno espaçamento entre os recortes para evitar sobreposição.  
✅ **Rotação das peças:** Retângulos podem ser girados em 0° ou 90°, e diamantes podem ser girados de 0° a 90° em incrementos de 10°.  
✅ **Verificação de ocupação:** Antes de posicionar um recorte, o algoritmo verifica se o espaço está livre para evitar colisões.  

A cada nova solução gerada pelo **ACO**, o **FlexiblePacking** é chamado para validar e construir um layout viável.  

---

### **Especificações da Solução**  
- **Retângulos** podem ser rotacionados em **0° ou 90°**.  
- **Diamantes** podem ser rotacionados de **0° a 90° em incrementos de 10°**.  
- **Círculos** não são rotacionados (pois são simétricos).  
- **Margem de segurança** de **1 pixel** é aplicada entre as peças para evitar sobreposição.  

---

## **Requisitos**  
- **Python 3.6+** (necessário para f-strings)  
- **Numpy**  

---

## **Como Rodar o Projeto**  
1. Clone o repositório:  

   ```bash
   git clone <URL-do-repositório>
   cd <nome-da-pasta-do-repositório>
   ```

2. Execute o script principal:  

   ```bash
   python app.py
   ```

Cada execução exibirá:  
- **O layout inicial dos recortes na chapa.**  
- **O layout otimizado gerado pelo ACO.**  
- **Estatísticas sobre o aproveitamento da chapa e o tempo de execução.**  

---


## **Resultados Visuais**  

- **Layout otimizado usando ACO:**
![ACO-FINAL2](https://github.com/user-attachments/assets/ef8483f3-2886-4272-bb9f-6cf23b6c4e38)


