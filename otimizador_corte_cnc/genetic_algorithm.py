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

        #Adiciona indivíduo inicial na população
        self.POP.append(copy.deepcopy(self.initial_layout))

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
                margem=5
            )
            individuo_empacotado = gerar_individuo.empacotar()
            self.POP.append(individuo_empacotado)

    def evaluate(self):
        # Evaluate the fitness of individuals based on available parts.
        pass

    def genetic_operators(self):
        # Execute genetic operators (crossover, mutation, etc.) to evolve the population.
        pass

    def run(self):
        # Main loop of the evolutionary algorithm.

        # Temporary return statement to avoid errors
        self.initialize_population()
        self.optimized_layout = self.initial_layout
        return self.optimized_layout

    def optimize_and_display(self):
        """
        Displays the initial layout, runs the optimization algorithm,
        and displays the optimized layout using the mixin's display_layout method.
        """
        # Display initial layout
        #self.display_layout(self.initial_layout, title="Initial Layout - Genetic Algorithm")
        
        # Run the optimization algorithm (updates self.melhor_individuo)
        self.optimized_layout = self.run()

        for individuos in self.POP:
                self.display_layout(individuos, title="Optimized Layout - Genetic Algorithm - Individuos")
        
        # Display optimized layout
        #self.display_layout(self.optimized_layout, title="Optimized Layout - Genetic Algorithm")
        return self.optimized_layout