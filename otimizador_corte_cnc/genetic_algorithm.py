from common.layout_display import LayoutDisplayMixin
import random
import copy
import math
import numpy as np
from flexible_packing import FlexiblePacking

class GeneticAlgorithm(LayoutDisplayMixin):
    def __init__(self, TAM_POP, recortes_disponiveis, sheet_width, sheet_height, numero_geracoes=100):
        print("Algoritmo Genético para Otimização do Corte de Chapa. Executado por Iad.")
        self.TAM_POP = TAM_POP
        self.initial_layout = recortes_disponiveis  # Available cut parts
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.POP = []
        self.POP_AUX = []
        self.aptidao = []
        self.numero_geracoes = numero_geracoes
        self.initialize_population()
        self.melhor_aptidoes = []
        self.optimized_layout = None 

    def initialize_population(self):
        """
        Inicializa a população criando indivíduos com:
        - Ordem aleatória dos recortes.
        - Rotação aleatória (0 a 90, de 10 em 10) para peças rotacionáveis.
        - Configurações aleatórias de varredura.
        """

        print("Criando população inicial...")

        # Os primeiros indivíduos serão gerados em configurações fixas que tem maior possibilidade de criação de um indivíduo válido
        fixed_configs = [
            {"order": "desc", "varrer_esquerda_direita": True,  "varrer_cima_baixo": True,  "priorizar_horizontal": True},   # 1º: Ordenar do maior para menor, varredura original.
            {"order": "desc", "varrer_esquerda_direita": False, "varrer_cima_baixo": False, "priorizar_horizontal": True},   # 2º: Descendente, varredura: direita→esquerda e de baixo para cima.
            {"order": "desc", "varrer_esquerda_direita": True,  "varrer_cima_baixo": True,  "priorizar_horizontal": False},  # 3º: Descendente, varredura: de cima para baixo (alterando a prioridade para vertical).
            {"order": "desc", "varrer_esquerda_direita": False, "varrer_cima_baixo": True,  "priorizar_horizontal": True},   # 4º: Descendente, varredura: de cima para baixo, mas com horizontal invertida.
            {"order": "asc",  "varrer_esquerda_direita": False, "varrer_cima_baixo": False, "priorizar_horizontal": True},   # 5º: Ascendente (menor para maior), varredura: direita→esquerda e de baixo para cima.
            {"order": "asc",  "varrer_esquerda_direita": True,  "varrer_cima_baixo": True,  "priorizar_horizontal": True},   # 6º: Ascendente, varredura: de cima para baixo (original).
            {"order": "asc",  "varrer_esquerda_direita": False, "varrer_cima_baixo": True,  "priorizar_horizontal": True}    # 7º: Ascendente, varredura: de cima para baixo com horizontal invertida.
        ]
        n_fixed = len(fixed_configs)

        for i in range(self.TAM_POP):
            # Cria uma cópia dos recortes disponíveis
            individuo = copy.deepcopy(self.initial_layout)
            
            if i < n_fixed:
                # Usa a configuração fixa
                config = fixed_configs[i]
                if config["order"] == "desc":
                    # Ordena do maior para o menor (baseado na área)
                    individuo.sort(key=lambda p: self.get_area(p), reverse=True)
                else:
                    # Ordena do menor para o maior
                    individuo.sort(key=lambda p: self.get_area(p), reverse=False)
                varrer_esquerda_direita = config["varrer_esquerda_direita"]
                varrer_cima_baixo = config["varrer_cima_baixo"]
                priorizar_horizontal = config["priorizar_horizontal"]
            else:
                # Para os demais indivíduos, usa ordem e varredura aleatória
                random.shuffle(individuo)
                varrer_esquerda_direita = random.choice([True, False])
                varrer_cima_baixo = random.choice([True, False])
                priorizar_horizontal = random.choice([True, False])
            
            # Cria o indivíduo usando o FlexiblePacking com as configurações definidas
            gerar_individuo = FlexiblePacking(
                sheet_width=self.sheet_width,
                sheet_height=self.sheet_height,
                recortes_disponiveis=individuo,
                varrer_esquerda_direita=varrer_esquerda_direita,
                varrer_cima_baixo=varrer_cima_baixo,
                priorizar_horizontal=priorizar_horizontal,
                margem=1
            )
            individuo_empacotado = gerar_individuo.empacotar()
            self.POP.append(individuo_empacotado)
            
        print("População inicial criada!")

    def get_area(self, peca):
        if peca["tipo"] == "retangular":
            return peca["largura"] * peca["altura"]
        elif peca["tipo"] == "circular":
            return math.pi * (peca["r"] ** 2)
        elif peca["tipo"] == "diamante":
            return (peca["largura"] * peca["altura"]) / 2
        return 0

    def get_bounding_box(self, peca):
        if peca["tipo"] == "circular":
            return 2 * peca["r"], 2 * peca["r"]
        angulo = math.radians(peca["rotacao"])
        largura_original = peca.get("largura", 2 * peca.get("r", 0))
        altura_original = peca.get("altura", 2 * peca.get("r", 0))
        largura_rotacionada = abs(largura_original * math.cos(angulo)) + abs(altura_original * math.sin(angulo))
        altura_rotacionada = abs(largura_original * math.sin(angulo)) + abs(altura_original * math.cos(angulo))
        return int(round(largura_rotacionada)), int(round(altura_rotacionada))
    
    def get_circle_mask(self, raio):
        """
        Gera uma máscara booleana para um círculo com raio 'raio' e margem self.margem.
        A máscara terá tamanho = 2*(raio + margem) + 1 e True para os pontos dentro do círculo expandido.
        """
        total = raio
        # Cria uma grade de coordenadas
        y, x = np.ogrid[-total:total+1, -total:total+1]
        mask = x**2 + y**2 <= (raio)**2
        return mask
    
    def is_point_inside_diamond(self, px, py, vertices):
        """
        Verifica se um ponto (px, py) está dentro do diamante definido por seus vértices.
        Utiliza a fórmula do produto vetorial para determinar se está dentro do losango.
        """
        A, B, C, D = vertices  # Vértices do diamante em ordem

        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

        b1 = sign((px, py), A, B) < 0.0
        b2 = sign((px, py), B, C) < 0.0
        b3 = sign((px, py), C, D) < 0.0
        b4 = sign((px, py), D, A) < 0.0

        return b1 == b2 == b3 == b4
    
    def get_rotated_vertices(self, peca, x, y):
        """
        Retorna os vértices reais do diamante após a rotação, preservando seu tamanho original.
        """
        largura = peca["largura"]
        altura = peca["altura"]
        cx, cy = x + largura / 2, y + altura / 2 
        angulo = math.radians(peca["rotacao"])

        # Vértices antes da rotação
        vertices_originais = [
            (cx, y),  # Topo
            (x + largura, cy),  # Direita
            (cx, y + altura),  # Base
            (x, cy)  # Esquerda
        ]

        # Aplica rotação a cada vértice
        vertices_rotacionados = [
            (
                (vx - cx) * math.cos(angulo) - (vy - cy) * math.sin(angulo) + cx,
                (vx - cx) * math.sin(angulo) + (vy - cy) * math.cos(angulo) + cy
            )
            for vx, vy in vertices_originais
        ]

        return vertices_rotacionados
    
    def evaluate(self):
        """
        Avalia cada layout (indivíduo) da população com base em:
        - Aproveitamento da área (usada em relação à área total da chapa).
        - Penalizações para sobreposição (contabilizada apenas nas áreas realmente ocupadas pelas peças).
        - Penalizações para peças fora dos limites.
        - Penalizações se houver peças faltantes.
        """
        self.aptidao = []  # Reinicia as aptidões

        # Parâmetros de penalização (ajustáveis conforme experimentos)
        penalty_overlap_factor = 0.001   # Penalidade por célula sobreposta
        penalty_missing_factor = 1.0       # Penalidade por cada peça faltante
        penalty_out_of_bounds_factor = 0.1 # Penalidade por peça fora dos limites

        total_sheet_area = self.sheet_width * self.sheet_height

        # Para cada layout da população:
        for individual in self.POP:
            used_area = 0.0
            out_of_bounds_penalty = 0.0

            # Se o layout tiver menos peças que o esperado, aplica penalidade
            missing_penalty = (len(self.initial_layout) - len(individual)) * penalty_missing_factor if len(individual) < len(self.initial_layout) else 0

            # Cria um grid para marcar as células efetivamente ocupadas
            grid = np.zeros((self.sheet_width, self.sheet_height), dtype=int)

            # Processa cada peça do layout
            for peca in individual:
                used_area += self.get_area(peca)
                width, height = self.get_bounding_box(peca)
                x = peca["x"]
                y = peca["y"]

                # Verifica se a peça está fora dos limites (bounding box)
                if x < 0 or y < 0 or x + width > self.sheet_width or y + height > self.sheet_height:
                    out_of_bounds_penalty += penalty_out_of_bounds_factor

                # Marcação real no grid dependendo do tipo da peça:
                if peca["tipo"] == "circular":
                    raio = peca["r"]
                    centro_x = x + raio
                    centro_y = y + raio
                    # Gera a máscara do círculo (com margem)
                    mask = self.get_circle_mask(raio)
                    mask_shape = mask.shape
                    # Define a posição inicial para aplicar a máscara no grid
                    start_x = int(round(centro_x - (raio)))
                    start_y = int(round(centro_y - (raio )))

                    for i in range(mask_shape[0]):
                        for j in range(mask_shape[1]):
                            if mask[i, j]:
                                gx = start_x + i
                                gy = start_y + j
                                if 0 <= gx < self.sheet_width and 0 <= gy < self.sheet_height:
                                    grid[gx, gy] += 1

                elif peca["tipo"] == "diamante":
                    # Obtém os vértices rotacionados do diamante
                    vertices = self.get_rotated_vertices(peca, x, y)
                    min_x = max(int(min(v[0] for v in vertices)), 0)
                    max_x = min(int(max(v[0] for v in vertices)), self.sheet_width - 1)
                    min_y = max(int(min(v[1] for v in vertices)), 0)
                    max_y = min(int(max(v[1] for v in vertices)), self.sheet_height - 1)
                    for i in range(min_x, max_x + 1):
                        for j in range(min_y, max_y + 1):
                            if self.is_point_inside_diamond(i, j, vertices):
                                grid[i, j] += 1

                else:  # Peças retangulares – sua forma coincide com o bounding box
                    for i in range(x, min(x + width, self.sheet_width)):
                        for j in range(y, min(y + height, self.sheet_height)):
                            grid[i, j] += 1

            # Penalização por sobreposição: para cada célula com valor > 1, desconta o excesso
            overlap_cells = grid[grid > 1] - 1  # Cada célula extra além da primeira conta como sobreposição
            overlap_penalty = penalty_overlap_factor * np.sum(overlap_cells)

            # Cálculo do aproveitamento da área
            area_utilization = used_area / total_sheet_area

            # Combina as métricas: quanto maior a área utilizada e menor as penalizações, melhor o fitness
            fitness = area_utilization - (overlap_penalty + missing_penalty + out_of_bounds_penalty)
            self.aptidao.append(fitness)

    def genetic_operators(self):
        """
        Executa o ciclo evolutivo do algoritmo genético:
        1. Avalia a população atual e registra a aptidão.
        2. Seleciona indivíduos por torneio e gera descendentes via cruzamento simples.
        3. Aplica mutação a uma fração dos descendentes.
        4. Atualiza a população com os novos indivíduos.
        Retorna o melhor indivíduo encontrado ao final das gerações.
        """ 
        
        # Percentuais para os operadores genéticos:
        tx_cruzamento_simples = 30   # 30% dos indivíduos serão gerados via cruzamento simples
        tx_mutacao = 5               # 2% dos indivíduos sofrerão mutação

        print("Iniciando a execução dos operadores genéticos...")

        # Loop para o número de gerações definidas
        for geracao in range(self.numero_geracoes):
            # Reinicia a população auxiliar para a próxima geração
            self.POP_AUX = []

            # Avalia a população atual e armazena as aptidões
            self.evaluate()
            melhor_index, melhor_fitness = self.pegar_melhor_individuo()
            self.melhor_aptidoes.append(melhor_fitness)

            print(f"Geração {geracao}: Melhor Aptidão = {melhor_fitness}")

            # --- Elitismo ---
            elitismo_count = int(self.TAM_POP * 0.01)
            self.elitismo(elitismo_count)

            # --- Cruzamento Simples ---
            qtd_crossover = int(self.TAM_POP * tx_cruzamento_simples / 100)
            for _ in range(qtd_crossover):
                # Seleciona dois pais usando seleção por torneio
                pai1 = self.torneio(k=3)
                pai2 = self.torneio(k=3)
                # Garante que os pais sejam diferentes
                while pai1 == pai2:
                    pai2 = self.torneio(k=3)
                # Realiza o cruzamento simples e adiciona os descendentes na população auxiliar
                self.cruzamento_simples(pai1, pai2)

            # --- Mutação ---
            qtd_mutacao = int(self.TAM_POP * tx_mutacao / 100)
            for _ in range(qtd_mutacao):
                individuo_index = np.random.randint(0, self.TAM_POP)
                self.mutacao(individuo_index)

            # Substitui a população atual pelos descendentes gerados
            self.substituicao()

        # Após todas as gerações, exibe e retorna o melhor indivíduo encontrado
        melhor_index, _ = self.pegar_melhor_individuo()
        return self.POP[melhor_index]

    
    def torneio(self, k=3):
        """
        Seleção por torneio: seleciona k indivíduos aleatoriamente e retorna
        o índice do indivíduo com a maior aptidão.
        """
        indices = np.random.choice(range(len(self.POP)), k, replace=False)
        best_index = indices[0]
        best_fitness = self.aptidao[best_index]
        for idx in indices:
            if self.aptidao[idx] > best_fitness:
                best_index = idx
                best_fitness = self.aptidao[idx]
        return best_index

    def cruzamento_simples(self, pai1, pai2):
        """
        Realiza cruzamento simples entre os indivíduos (layouts) de índice pai1 e pai2.
        Assume que o layout é uma lista (ordem dos recortes) e combina a primeira metade
        de um pai com a segunda metade do outro.
        """
        # Obtemos os layouts dos pais
        layout_pai1 = self.POP[pai1]
        layout_pai2 = self.POP[pai2]
        gene_length = len(layout_pai1)
        
        # Realiza a divisão dos genes (peças) em duas metades
        metade = gene_length // 2
        # Cria os descendentes combinando as metades dos pais
        filho1 = copy.deepcopy(layout_pai1[:metade] + layout_pai2[metade:])
        filho2 = copy.deepcopy(layout_pai2[:metade] + layout_pai1[metade:])
        
        # Adiciona os descendentes na população auxiliar
        self.POP_AUX.append(filho1)
        self.POP_AUX.append(filho2)

    def mutacao(self, indice_individuo):
        """
        Realiza mutação em um indivíduo da população auxiliar.
        Aqui, a mutação pode ser, por exemplo, alterar aleatoriamente a rotação
        de uma peça (para peças que podem rotacionar) ou trocar a ordem de duas peças.
        """
        # Escolhe um indivíduo da POP_AUX (já gerado via cruzamento)
        individuo = self.POP_AUX[indice_individuo]
        gene_index = np.random.randint(0, len(individuo))
        peca = individuo[gene_index]
        
        # Se a peça for rotacionável, altera sua rotação para um valor aleatório válido
        if peca["tipo"] ==  "diamante":
            peca["rotacao"] = random.choice(range(0, 100, 10))
        elif peca["tipo"] == "retangular":
            peca["rotacao"] = random.choice([0, 90])
    
    def elitismo(self, qtd):
        """
        Seleciona os 'qtd' melhores indivíduos com aptidão > 0, se houver,
        ou os melhores de toda a população caso nenhum indivíduo tenha aptidão positiva.
        Esses indivíduos são adicionados à população auxiliar (self.POP_AUX),
        garantindo que os melhores layouts sejam preservados para a próxima geração.
        """
        
        # Filtra indivíduos com aptidão maior que 0
        apt_index = [(self.aptidao[i], i) for i in range(len(self.POP)) if self.aptidao[i] > 0]
        if not apt_index:  # Se nenhum tiver aptidão > 0, usa todos
            apt_index = [(self.aptidao[i], i) for i in range(len(self.POP))]
        
        # Ordena os indivíduos (com aptidão > 0) de forma decrescente
        apt_index_sorted = sorted(apt_index, key=lambda x: x[0], reverse=True)
        
        # Adiciona os melhores indivíduos à população auxiliar
        for i in range(int(qtd)):
            idx = apt_index_sorted[i % len(apt_index_sorted)][1]
            self.POP_AUX.append(copy.deepcopy(self.POP[idx]))


    def pegar_melhor_individuo(self):
        apt = max(self.aptidao)
        quem = self.aptidao.index(apt)
        return quem, apt
        
    def substituicao(self):
        self.POP = self.POP_AUX.copy()

    def run(self):
        # Main loop of the evolutionary algorithm.
        best_individual = self.genetic_operators()
    
        # Salva e retorna o melhor layout encontrado
        self.optimized_layout = best_individual
        return self.optimized_layout

    def optimize_and_display(self):
        """
        Displays the initial layout, runs the optimization algorithm,
        and displays the optimized layout using the mixin's display_layout method.
        """
        # Display initial layout
        self.display_layout(self.initial_layout, title="Initial Layout - Genetic Algorithm")
        
        # Run the optimization algorithm (updates self.melhor_individuo)
        self.optimized_layout = self.run()
        
        # Display optimized layout
        self.display_layout(self.optimized_layout, title="Optimized Layout - Genetic Algorithm")
        return self.optimized_layout