import copy
import numpy as np
from common.packing_base import PackingBase

"""
Implementa um algoritmo flexível de empacotamento de peças em uma chapa, permitindo diferentes estratégias de posicionamento.

- Permite configurar a ordem de varredura da chapa:
    - Da esquerda para a direita ou da direita para a esquerda.
    - De cima para baixo ou de baixo para cima.
- Suporta peças retangulares, circulares e diamantes, aplicando rotações configuráveis (0 a 90 graus em incrementos de 10 graus).
- Utiliza uma matriz de ocupação (grid) para verificar colisões e garantir que as peças não se sobreponham.
- Adiciona uma margem opcional entre os recortes para evitar cortes imprecisos ou colisões mecânicas.
- Mantém a ordem original dos recortes na entrada.

Essa abordagem é ideal para otimizar o corte de materiais em processos industriais, como fabricação de móveis, corte de chapas metálicas, vidro, madeira e tecidos.
"""
class FlexiblePacking(PackingBase):
    def __init__(self, sheet_width, sheet_height, recortes_disponiveis, varrer_esquerda_direita=True, varrer_cima_baixo=True,
                 priorizar_horizontal=True, margem=1):
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.recortes = recortes_disponiveis
        self.layout = []
        self.grid = np.zeros((sheet_width, sheet_height), dtype=int)
        self.margem = margem
        self.varrer_esquerda_direita = varrer_esquerda_direita
        self.varrer_cima_baixo = varrer_cima_baixo	
        self.priorizar_horizontal = priorizar_horizontal

    def cabe_no_espaco(self, peca, x, y):
        """
        Verifica se a peça pode ser colocada sem ultrapassar os limites da chapa e sem sobreposição.
        Agora adiciona uma margem de 1 pixel entre os recortes.
        """

        if peca["tipo"] == "circular":
            raio = peca["r"]
            centro_x = x + raio
            centro_y = y + raio

            # Verifica se o círculo (com margem) está dentro dos limites
            if (centro_x - raio - self.margem < 0 or 
                centro_x + raio + self.margem > self.sheet_width or 
                centro_y - raio - self.margem < 0 or 
                centro_y + raio + self.margem > self.sheet_height):
                return False

            # Obtém a máscara do círculo
            mask = self.get_circle_mask(raio)
            mask_shape = mask.shape

            # Determina a posição inicial da máscara no grid
            start_x = int(round(centro_x - (raio + self.margem)))
            start_y = int(round(centro_y - (raio + self.margem)))

            # Verifica a sobreposição usando a máscara
            for i in range(mask_shape[0]):
                for j in range(mask_shape[1]):
                    if mask[i, j]:
                        grid_x = start_x + i
                        grid_y = start_y + j
                        if grid_x < 0 or grid_x >= self.sheet_width or grid_y < 0 or grid_y >= self.sheet_height:
                            continue
                        if self.grid[grid_x, grid_y] == 1:
                            return False

        elif peca["tipo"] == "diamante":
            vertices = self.get_rotated_vertices(peca, x, y)

            for vx, vy in vertices:
                if not (self.margem <= vx < self.sheet_width - self.margem and self.margem <= vy < self.sheet_height - self.margem):
                    return False

            min_x = max(int(min(v[0] for v in vertices)) - self.margem, 0)
            max_x = min(int(max(v[0] for v in vertices)) + self.margem, self.sheet_width - 1)
            min_y = max(int(min(v[1] for v in vertices)) - self.margem, 0)
            max_y = min(int(max(v[1] for v in vertices)) + self.margem, self.sheet_height - 1)

            range_x = range(min_x, max_x + 1) if self.varrer_esquerda_direita else range(max_x, min_x - 1, -1)
            range_y = range(min_y, max_y + 1) if self.varrer_cima_baixo else range(max_y, min_y - 1, -1)

            for i in range_x:
                for j in range_y:
                    if self.is_point_inside_diamond(i, j, vertices):
                        if self.grid[i, j] == 1:
                            return False

        else:
            largura, altura = self.get_bounding_box(peca)

            if (
                x - self.margem < 0 or 
                y - self.margem < 0 or 
                x + largura + self.margem > self.sheet_width or 
                y + altura + self.margem > self.sheet_height
            ):
                return False  

            range_x = range(-self.margem, largura + self.margem) if self.varrer_esquerda_direita else range(largura + self.margem - 1, -self.margem - 1, -1)
            range_y = range(-self.margem, altura + self.margem) if self.varrer_cima_baixo else range(altura + self.margem - 1, -self.margem - 1, -1)

            for i in range_x:
                for j in range_y:
                    if 0 <= x + i < self.sheet_width and 0 <= y + j < self.sheet_height:
                        if self.grid[x + i, y + j] == 1:
                            return False

        return True

    def ajustar_posicao_para_dentro(self, peca, x, y):
        """
        Ajusta a posição da peça para garantir que ela não ultrapasse os limites da chapa.
        """
        largura, altura = self.get_bounding_box(peca)

        # Se estiver saindo da chapa, ajusta o x e y
        if x + largura > self.sheet_width:
            x = self.sheet_width - largura
        if y + altura > self.sheet_height:
            y = self.sheet_height - altura

        return x, y

    def marcar_ocupacao(self, peca):
        """
        Marca a área ocupada pela peça na matriz de ocupação, garantindo uma margem de 1 pixel.
        """
        x, y = peca["x"], peca["y"]

        if peca["tipo"] == "circular":
            raio = peca["r"]
            centro_x = x + raio
            centro_y = y + raio

            mask = self.get_circle_mask(raio)
            mask_shape = mask.shape
            start_x = int(round(centro_x - (raio + self.margem)))
            start_y = int(round(centro_y - (raio + self.margem)))
            
            for i in range(mask_shape[0]):
                for j in range(mask_shape[1]):
                    if mask[i, j]:
                        grid_x = start_x + i
                        grid_y = start_y + j
                        if 0 <= grid_x < self.sheet_width and 0 <= grid_y < self.sheet_height:
                            self.grid[grid_x, grid_y] = 1

        elif peca["tipo"] == "diamante":
            vertices = self.get_rotated_vertices(peca, x, y)

            min_x = max(int(min(v[0] for v in vertices)) - self.margem, 0)
            max_x = min(int(max(v[0] for v in vertices)) + self.margem, self.sheet_width - 1)
            min_y = max(int(min(v[1] for v in vertices)) - self.margem, 0)
            max_y = min(int(max(v[1] for v in vertices)) + self.margem, self.sheet_height - 1)

            range_x = range(min_x, max_x + 1) if self.varrer_esquerda_direita else range(max_x, min_x - 1, -1)
            range_y = range(min_y, max_y + 1) if self.varrer_cima_baixo else range(max_y, min_y - 1, -1)

            for i in range_x:
                for j in range_y:
                    if self.is_point_inside_diamond(i, j, vertices):
                        if 0 <= i < self.sheet_width and 0 <= j < self.sheet_height:
                            self.grid[i, j] = 1

        else:  
            largura, altura = self.get_bounding_box(peca)

            range_x = range(-self.margem, largura + self.margem) if self.varrer_esquerda_direita else range(largura + self.margem - 1, -self.margem - 1, -1)
            range_y = range(-self.margem, altura + self.margem) if self.varrer_cima_baixo else range(altura + self.margem - 1, -self.margem - 1, -1)

            for i in range_x:
                for j in range_y:
                    if 0 <= x + i < self.sheet_width and 0 <= y + j < self.sheet_height:
                        self.grid[x + i, y + j] = 1

    
    def empacotar(self):
        """ Organiza as peças dentro da chapa considerando as configurações de varredura e margem. """

        # Reinicia layout e grid para evitar resíduos de execuções anteriores
        self.layout = []
        self.grid = np.zeros((self.sheet_width, self.sheet_height), dtype=int)

        for peca in self.recortes:
            encontrou_posicao = False
            
            # Retângulos só poderão rotacionar em 0 ou 90
            if peca["tipo"] == 'retangular':
                rotacoes = [0, 90]
            else:
                # Mantém a rotação original primeiro, depois testa outras de 0 a 90 (se necessário)
                rotacoes = [0] if peca["tipo"] == "circular" else [peca.get("rotacao", 0)] + [r for r in range(0, 100, 10) if r != peca.get("rotacao", 0)]
            
            for rotacao in rotacoes:
                peca["rotacao"] = rotacao
                largura, altura = self.get_bounding_box(peca)

                # Define as ordens de varredura da chapa
                range_x = range(0, self.sheet_width - largura + 1) if self.varrer_esquerda_direita else range(self.sheet_width - largura, -1, -1)
                range_y = range(0, self.sheet_height - altura + 1) if self.varrer_cima_baixo else range(self.sheet_height - altura, -1, -1)

                # Alterna entre percorrer horizontalmente ou verticalmente
                if self.priorizar_horizontal:
                    iteracoes = [(x, y) for y in range_y for x in range_x]
                else:
                    iteracoes = [(x, y) for x in range_x for y in range_y]

                # Testa cada posição disponível
                for x, y in iteracoes:
                    if self.cabe_no_espaco(peca, x, y):
                        peca["x"], peca["y"] = x, y
                        self.layout.append(copy.deepcopy(peca))
                        self.marcar_ocupacao(peca)
                        encontrou_posicao = True
                        break

                # Se encontrou um local, não precisa testar outras rotações
                if encontrou_posicao:
                    break

        return self.layout