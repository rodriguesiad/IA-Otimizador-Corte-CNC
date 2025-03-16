from common.layout_display import LayoutDisplayMixin
from flexible_packing import FlexiblePacking
from common.packing_base import PackingBase
import random
import copy
import time
import numpy as np

class AntColony(LayoutDisplayMixin, PackingBase):
    def __init__(self, num_ants, num_iterations, sheet_width, sheet_height, recortes_disponiveis):
        """
        Initializes the Ant Colony optimizer.
        :param num_ants: Number of ants.
        :param num_iterations: Number of iterations to run.
        :param sheet_width: Width of the cutting sheet.
        :param sheet_height: Height of the cutting sheet.
        :param recortes_disponiveis: List of available parts (JSON structure).
        """
        print("Ant Colony para Otimização do Corte de Chapa. Executado por Iad.")

        self.num_ants = num_ants
        self.num_iterations = num_iterations
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.initial_layout = recortes_disponiveis
        self.optimized_layout = None
        print("Ant Colony Optimization Initialized.")

    def initialize_pheromones(self):
        """
        Inicializa as estruturas de feromônio para as decisões:
          - Configuração de varredura: opções para a ordem de varredura da chapa.
          - Ordem dos recortes: uma lista de feromônios, um para cada recorte.
          - Rotação: níveis de feromônio para cada ângulo possível (0, 10, ..., 90).
          - Direção de priorização: define se a busca será priorizada horizontalmente ou verticalmente.
        Inicializamos todos os níveis com 1.0.
        """

        self.pheromones_scan = {
            "left_to_right_top_to_bottom": 1.0,
            "right_to_left_bottom_to_top": 1.0,
            "left_to_right_bottom_to_top": 1.0,
            "right_to_left_top_to_bottom": 1.0
        }
        self.pheromones_order = [1.0 for _ in range(len(self.initial_layout))]
        self.pheromones_rotation = {angle: 1.0 for angle in range(0, 100, 10)}
        self.pheromones_direction = {"horizontal": 1.0, "vertical": 1.0}

    def construct_solution(self, ant):
        # 1. Seleção da configuração de varredura
        scan_options = list(self.pheromones_scan.keys())
        scan_weights = [self.pheromones_scan[opt] for opt in scan_options]
        selected_scan = random.choices(scan_options, weights=scan_weights, k=1)[0]
        
        if selected_scan == "left_to_right_top_to_bottom":
            varrer_esquerda_direita = True
            varrer_cima_baixo = True
        elif selected_scan == "right_to_left_bottom_to_top":
            varrer_esquerda_direita = False
            varrer_cima_baixo = False
        elif selected_scan == "left_to_right_bottom_to_top":
            varrer_esquerda_direita = True
            varrer_cima_baixo = False
        elif selected_scan == "right_to_left_top_to_bottom":
            varrer_esquerda_direita = False
            varrer_cima_baixo = True

        # 2. Ordenação dos recortes
        recortes = copy.deepcopy(self.initial_layout)
        recortes.sort(key=lambda p: self.get_area(p), reverse=True)
        
        # 3. Escolha da rotação para cada recorte
        if random.random() < 0.1:
            for peca in recortes:
                if peca["tipo"] ==  "diamante":
                    angles = list(self.pheromones_rotation.keys())
                    rotation_weights = [self.pheromones_rotation[angle] for angle in angles]
                    peca["rotacao"] = random.choices(angles, weights=rotation_weights, k=1)[0]
                elif peca["tipo"] == "retangular":
                    angles = [0,90]
                    rotation_weights = [self.pheromones_rotation[angle] for angle in angles]
                    peca["rotacao"] = random.choices(angles, weights=rotation_weights, k=1)[0]
                else:
                    peca["rotacao"] = 0

        # 4. Seleção da priorização com base no feromônio
        direction_choice = random.choices(
            ["horizontal", "vertical"],
            weights=[self.pheromones_direction["horizontal"], self.pheromones_direction["vertical"]],
            k=1
        )[0]
        priorizar_horizontal = (direction_choice == "horizontal")

        # 5. Constrói o layout com FlexiblePacking
        gerar_layout = FlexiblePacking(
            sheet_width=self.sheet_width,
            sheet_height=self.sheet_height,
            recortes_disponiveis=recortes,
            varrer_esquerda_direita=varrer_esquerda_direita,
            varrer_cima_baixo=varrer_cima_baixo,
            priorizar_horizontal=priorizar_horizontal,
            margem=1
        )
        layout = gerar_layout.empacotar()
        
        print('Layout criado!')
        # Retorne o layout juntamente com as escolhas feitas
        return {"layout": layout, "scan": selected_scan, "direction": direction_choice}


    def update_pheromones(self, solutions):
        """
        Atualiza os níveis de feromônio com base nas soluções construídas pelas formigas.
        Para cada solução, deposita uma quantidade de feromônio proporcional à sua qualidade.
        Aqui, assumimos que uma solução melhor tem um valor de qualidade (fitness) maior.
        Atualizamos os feromônios das decisões (varredura, ordem e rotação) que levaram à solução.
        """
        for sol in solutions:
            quality = sol["quality"]
            # Atualiza feromônios para a configuração de varredura
            selected_scan = sol["scan"]
            self.pheromones_scan[selected_scan] += quality

            # Atualiza feromônios para a rotação de cada peça rotacionável
            for angle in sol["rotation"].values():
                self.pheromones_rotation[angle] += quality

            # Atualiza feromônios para a ordem dos recortes
            for i in range(len(self.pheromones_order)):
                self.pheromones_order[i] += quality * 0.01  # fator pequeno para atualização

            # Atualiza feromônios para a direção de priorização
            direction = sol.get("direction", "horizontal")
            self.pheromones_direction[direction] += quality

    def evaporate_pheromones(self):
        """
        Aplica evaporação aos feromônios para diminuir os níveis de feromônio existentes,
        evitando que valores muito altos impeçam a exploração de novas soluções.
        Multiplica cada feromônio por um fator de evaporação (por exemplo, 0.9).
        """
        evap_factor = 0.9

        for key in self.pheromones_scan:
            self.pheromones_scan[key] *= evap_factor

        for angle in self.pheromones_rotation:
            self.pheromones_rotation[angle] *= evap_factor

        # Atualiza a lista de feromônios para ordem
        self.pheromones_order = [val * evap_factor for val in self.pheromones_order]

        for key in self.pheromones_direction:
            self.pheromones_direction[key] *= evap_factor
    
    def evaluate_layout(self, layout):
        """
        Avalia a qualidade de um layout considerando:
        - Aproveitamento da área (área utilizada / área total da chapa);
        - Penalizações para sobreposição (somente nas células ocupadas em excesso);
        - Penalizações para peças fora dos limites;
        - Penalizações se houver peças faltantes.
        
        Retorna um valor numérico, onde valores maiores indicam layouts melhores.
        """
        total_sheet_area = self.sheet_width * self.sheet_height
        used_area = 0.0
        out_of_bounds_penalty = 0.0

        # Se o layout tiver menos peças que o esperado, aplica penalidade
        missing_penalty = (len(self.initial_layout) - len(layout)) * 1.0 if len(layout) < len(self.initial_layout) else 0

        # Cria um grid para marcar as células efetivamente ocupadas
        grid = np.zeros((self.sheet_width, self.sheet_height), dtype=int)

        for peca in layout:
            used_area += self.get_area(peca)
            width, height = self.get_bounding_box(peca)
            x = peca["x"]
            y = peca["y"]

            # Verifica se o bounding box da peça está fora dos limites
            if x < 0 or y < 0 or x + width > self.sheet_width or y + height > self.sheet_height:
                out_of_bounds_penalty += 0.1

            # Marcação no grid, de acordo com o tipo da peça:
            if peca["tipo"] == "circular":
                raio = peca["r"]
                centro_x = x + raio
                centro_y = y + raio
                mask = self.get_circle_mask(raio, margem=0)  # Usamos margem=0 para cálculo de área efetiva
                mask_shape = mask.shape
                start_x = int(round(centro_x - raio))
                start_y = int(round(centro_y - raio))
                for i in range(mask_shape[0]):
                    for j in range(mask_shape[1]):
                        if mask[i, j]:
                            gx = start_x + i
                            gy = start_y + j
                            if 0 <= gx < self.sheet_width and 0 <= gy < self.sheet_height:
                                grid[gx, gy] += 1

            elif peca["tipo"] == "diamante":
                vertices = self.get_rotated_vertices(peca, x, y)
                min_x = max(int(min(v[0] for v in vertices)), 0)
                max_x = min(int(max(v[0] for v in vertices)), self.sheet_width - 1)
                min_y = max(int(min(v[1] for v in vertices)), 0)
                max_y = min(int(max(v[1] for v in vertices)), self.sheet_height - 1)
                for i in range(min_x, max_x + 1):
                    for j in range(min_y, max_y + 1):
                        if self.is_point_inside_diamond(i, j, vertices):
                            grid[i, j] += 1

            else:  # Retangular
                for i in range(x, min(x + width, self.sheet_width)):
                    for j in range(y, min(y + height, self.sheet_height)):
                        grid[i, j] += 1

        # Penalização por sobreposição: cada célula ocupada mais de uma vez gera penalização
        overlap_cells = grid[grid > 1] - 1
        overlap_penalty = 0.001 * np.sum(overlap_cells)

        area_utilization = used_area / total_sheet_area

        quality = area_utilization - (overlap_penalty + missing_penalty + out_of_bounds_penalty)
        return quality

    def run(self):
        """
        Loop principal do algoritmo de Colônia de Formigas:
        1. Inicializa os feromônios.
        2. Para cada iteração:
            - Cada formiga constrói uma solução.
            - Avalia a qualidade de cada solução (usando um critério, por exemplo, aproveitamento de área).
            - Atualiza os feromônios com base nas soluções.
            - Aplica evaporação aos feromônios.
            - (Opcional) Armazena a melhor solução da iteração.
        3. Retorna a melhor solução encontrada (layout).
        """
        self.initialize_pheromones()

        # Lista para armazenar soluções de cada iteração
        best_overall = None
        best_overall_quality = -float("inf")
        avg_individual_times = []
        
        print("Iniciando o loop principal do Ant Colony...")
        
        for it in range(self.num_iterations):
            solutions = []
            total_individual_time = 0.0

            for ant in range(self.num_ants):
                start_time = time.time()

                sol = self.construct_solution(ant)
                layout = sol["layout"]
                quality = self.evaluate_layout(layout)
                solution_info = {
                    "layout": layout,
                    "scan": sol["scan"],
                    "rotation": {i: peca["rotacao"] for i, peca in enumerate(self.initial_layout) if peca["tipo"] in ["retangular", "diamante"]},
                    "direction": sol["direction"],
                    "quality": quality
                }

                solutions.append(solution_info)
                
                # Atualiza a melhor solução global
                if quality > best_overall_quality:
                    best_overall_quality = quality
                    best_overall = layout

                end_time = time.time()
                total_individual_time += (end_time - start_time)

            # Calcula tempo médio gasto pelas formigas para criar a solução
            avg_individual_time = total_individual_time / self.num_ants
            avg_individual_times.append(avg_individual_time)
            print(f"Iteração {it}: Melhor qualidade = {best_overall_quality} | Tempo médio por indivíduo = {avg_individual_time:.4f} s")

            # Atualiza os feromônios com base nas soluções desta iteração
            self.update_pheromones(solutions)
            # Aplica evaporação
            self.evaporate_pheromones()
        
        overall_avg_time = sum(avg_individual_times) / len(avg_individual_times)
        print(f"Tempo médio total por indivíduo: {overall_avg_time:.4f} s")
        
        self.optimized_layout = best_overall
        return self.optimized_layout

    def optimize_and_display(self):
        """
        Exibe o layout inicial, executa a otimização, exibe o layout otimizado e reporta:
        - Tempo de processamento total.
        - Aproveitamento da área (indicador de economia de matéria-prima).
        """
        # Exibe o layout inicial
        self.display_layout(self.initial_layout, title="Initial Layout - Ant Colony")
        
        # Registra o tempo de início
        start_time = time.time()
        
        # Executa a otimização
        self.optimized_layout = self.run()
        
        # Registra o tempo de término e calcula o tempo total
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calcula o aproveitamento da área do layout otimizado
        area_utilization = self.evaluate_layout(self.optimized_layout)
        
        # Exibe o layout otimizado
        self.display_layout(self.optimized_layout, title="Optimized Layout - Ant Colony")
        
        # Exibe os resultados de tempo e aproveitamento
        print(f"Tempo de processamento: {total_time:.2f} segundos")
        print(f"Aproveitamento da área: {area_utilization*100:.2f}%")
        
        return self.optimized_layout

    
