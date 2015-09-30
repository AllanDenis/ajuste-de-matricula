#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Otimização de grade de disciplinas, visando maximizar o número de aulas por semana
# ou juntar as folgas no mesmo dia

import arvore, dados, disciplina, view
import time
from itertools import combinations
import numpy as np
from scipy import linalg, sparse

from bintrees import BinaryTree as bt

agora = time.time
deps = dados.dependencias
historico = dados.historico

somaReq = deps.sum(axis=0)

# Lista de disciplinas que o aluno pode cursar.
cursaveis = historico.dot(deps)
cursaveis = cursaveis - historico

# Para evitar erro de div. por zero na disciplina nula e não permitir como cursável após divisão inteira
somaReq[0] = -2 # Qualquer valor < -1
for i in range(cursaveis.shape[1] - 1):
	cursaveis[0,i] //= somaReq[i]
somaReq[0] = 0

# Transforma em lista
cursaveis = list(cursaveis.getA()[0])

# Se o vetor de aprovação for inconsistente (disciplinas cumpridas sem todos os requisitos),
# o vetor de cursáveis terá valores negativos.
cursaveis = map(lambda x: 0 if x < 0 else x, cursaveis)
	
print "Vetor de requisitos (SC):\t", "".join(map(str, somaReq))
print "Vetor de aprovação (AP):\t", "".join(map(str, historico.toarray()[0]))
print "Vetor de cursáveis (DC):\t",		"".join(map(str, cursaveis))
print "Calculando as melhores grades para você. Aguarde..."

# Obtém os IDs das disciplinas cursáveis
cursaveis = set([x for x in xrange(len(cursaveis)) if cursaveis[x] == 1])
cursaveis = sorted(list(cursaveis - dados.disc_inativas))


# Retorna True se a grade não possuir conflitos
def grade_valida(g):
	return max(g) <= 1 # no máximo uma disciplina por aula

# Transforma um horário linear em uma matriz semanal, para impressão amigável
def formata_horario(h):
	return h.reshape(dados.dias_por_semana, dados.aulas_por_dia).T

def grade_pontuacao(g):
	periodo_max = 8
	aulas = aulas_da_grade(g, dados.horario)
	dias_vazios = formata_horario(aulas)
	dias_vazios = dias_vazios.sum(axis=0)
	dias_vazios = list(dias_vazios).count(0)
	pontos = list(aulas).count(1) # número de aulas
	bonus = 0 # % sobre os pontos
	bonus += 10e-2 * dias_vazios	# Privilegia dias de folga
	bonus += 2e-2 * (periodo_max - (np.mean(g)) / 10) # Privilegia as primeiras disciplinas
	bonus -= 1e-2 * (np.std(g)/np.mean(g)) # Penaliza o espalhamento de disciplinas
	pontos *= 1 + bonus
	return pontos

# Retorna uma matriz contendo o horário semanal das disciplinas da grade g
def aulas_da_grade(g, horario):
	une_disciplinas = lambda a, b: a + b
	horario_disciplinas = map(lambda d: dados.horario[d], g)
	return reduce(une_disciplinas, horario_disciplinas)

# Busca exaustiva (todas as combinações possíveis)
def busca_exaustiva(cursaveis):
	grades = []
	for i in xrange(1, 7):#len(cursaveis) + 1):
		print "Buscando grades com %d disciplina%s..." % (i, ("s" if i > 1 else ""))
		discs_tmp = []	# Lista de disciplinas para cada tamanho de grade
		inicio_tmp = agora()
		for grade in combinations(cursaveis, i):
			horario = dados.horario[0].copy()
			horario = map(lambda d: dados.horario[d], grade)
			horario = reduce(lambda a, b: a + b, horario)
			# for disc in grade:
				# horario = horario + dados.disciplinas[disc]
			if grade_valida(horario):
				# discs_tmp.append((horario, sorted(grade), grade_pontuacao(horario)))
				discs_tmp.append(sorted(grade))
		if len(discs_tmp) > 0:
			print "%d encontradas em %.3f segundos." % (len(discs_tmp), (agora() - inicio_tmp))
			grades.extend(discs_tmp)
		else:
			print "Nenhuma encontrada em %.3f segundos." % (agora() - inicio_tmp)
			break
	return grades

def busca_gulosa(cursaveis):
	grades = []
	cursaveis.sort()
	for i in range(len(cursaveis)):
		g = []
		for d in cursaveis:
			if grade_valida(aulas_da_grade(g + [d], dados.horario)):
				g.append(d)
		grades.append(g)
		cursaveis = cursaveis[1:] + cursaveis[0:1]
	return grades

inicio = agora()
# grades = busca_gulosa(cursaveis)
grades = busca_exaustiva(cursaveis)

print "\vBusca feita em %-.3fs." % (agora() - inicio)
print "Total de grades:\t%d" % len(grades)
print "Ordenando as grades..."
inicio = agora()
# Ordena as grades por quantidade de disciplinas e seus períodos
grades.sort(key=grade_pontuacao, reverse=True)
print "Ordenação feita em %.3f segundos." % (agora() - inicio)

'''		
for i in enumerate(grades[:]):#[:(5 if len(grades) > 5 else -1)]:
	print "\n(%d)\t%.2fpts\t" % (i[0] + 1, grade_pontuacao(i[1])), i[1]
	print formata_horario(aulas_da_grade(i[1], dados.horario))

'''

v = view.View()
v.dados = {}
v.dados["tamanhos"] = map(lambda g: len(g), grades)
v.dados["pontos"] = map(lambda g: grade_pontuacao(g), grades)
v.dados["popularidade"] = []

for g in grades:
	for i in g:
		v.dados["popularidade"].append(i)

# v.exibir()