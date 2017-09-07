import sys
import timeit
import os
import resource
import pprint
import random
import cPickle  
import pickle
import re

from Unification import unificar
from Parser import *
from Parser.CQparser import *
from CQ.Argumento import *
from CQ.Predicado import *
from CQ.SubObjetivo import *
from CQ.CQ import *
from CQ.SOComparacion import *
from TransformarFormula import *
from VariableSat import *
from MCD import *

archVistas = ''
archCons = ''

 
def generarReescrituras(exp, archV, archC, archVars, archTiempo, stdin, type, quantity, costFile):
    tiempoi = resource.getrusage(resource.RUSAGE_SELF)[0]
    generarReescrituras1(exp, archV, archC, archVars, stdin, type, quantity, costFile)
    tiempof = resource.getrusage(resource.RUSAGE_SELF)[0]
    
    fileobject = open(archTiempo, 'w')
    fileobject.write(str(tiempof-tiempoi))
    fileobject.close()

def generarReescrituras1(exp, archVistas, archCons, archVars, stdin, type, quantity, costFile):
    archVistas2 = archVistas.replace('.txt', '')

    vistas = cargarCQ(archVistas)

    #print archMod
    consultas = cargarCQ(archCons)

    for q in consultas:
        numeros = leerVars(archVars)
        lenQuery = len(q.cuerpo)
        if exp == 'Sat':
            generarReescMCD(numeros, stdin, vistas)
        if exp == 'SatRW':
            generarReescRW(numeros, stdin, lenQuery,q, vistas, type, quantity, costFile)
##        llamarzchaff(transf, archSalida)

def leerVars(archVars):
    fh = open(archVars,'r')
    numeros = pickle.load(fh)
    fh.close()
    return numeros 


def generarReescMCD_old(numeros, archMods, vistas):
    modelos = leerModelos(numeros, archMods)
    nmod = len(modelos)
    print "Modelos = ",nmod
    if nmod > 1:
        for mod in modelos:
            mcd = crearMCD(mod, vistas)
            if mcd != None:
                #print mod
                print mcd
    else:
        print "No hay MCDs"


def generarReescRWold(numeros, archMods, lenQuery, query, vistas):
    modelos = leerModelosRW(numeros, archMods, lenQuery, query, vistas)
    mcdsc = []
    for mod in modelos:
        mcds = []
        for mc in mod:
            mcd = crearMCD(mc, vistas)
            if mcd != None:
                #print mcd
                mcds.append(mcd)
        #print 
        mcdsc.append(mcds)
    rs = crearReescritura(mcdsc, query)
    pprint.pprint(rs)

def crearReescritura(mcdc, query):
    r = []
    seq = Seq()
    ecgeneral = unificar([k.ec for k in mcdc], query.variables())
    #print "ecgeneral", ecgeneral
    for m in mcdc:
        unif = m.obtUnificacion(ecgeneral)
        vis = m.vistaH.map_variables2(unif, seq)
        r.append(vis)

    cue = [v.cabeza for v in r]
    cab = query.cabeza.map_variables3(ecgeneral)
    res = CQ(cab, cue, [])
    return res


def crearMCD(mod, vistas):
    phictodo = {}
    gc=Set()
    for var in mod:
        if var[0] == 'v':
            numVista = var[2:len(var)-1]
            if numVista[0] == '-':
                return None
            else:
                vista = vistas[int(numVista)]
        elif var[0] == 't':
            i = var.find(',')
            phictodo.setdefault('X'+var[2:i],[]).append('X'+var[i+2:len(var)-1])
        elif var[0] == 'g':
            gc.add(var[2:len(var)-1])
    return MCD(phictodo, gc, vista)

def viewDictionary(costFile):
    ifile  = open(costFile, 'r')

    viewDic = {}

    for line in ifile:
        line = line[:-1]
        view = line.split('=')
        viewDic[view[0]] = view[1]

    return viewDic

def makeCost(value, viewCostDictionary):
    functions = value.split('),')
    cost = 0.0

    for each in functions:
        func = each.split('(')[0]
        func = func.split()
        cost += float(viewCostDictionary[func[0]].replace(',', '.'))

    return cost

def viewCosts(views, type, quantity, costFile):
    viewCostDictionary = viewDictionary(costFile)

    viewDic = {}

    for i, value in views.items():
        viewDic[i] = makeCost(value.split(':-')[1], viewCostDictionary)

    i = 0
    if type == '-top':
        for index, value in sorted(viewDic.iteritems(), key=lambda (k, v): (v, k), reverse=True):
            if int(i) < int(quantity):
                print views[index] + ', cost(' + str(value) + ')'
            i += 1

    elif type == '-bottom':
        for index, value in sorted(viewDic.iteritems(), key=lambda (k, v): (v, k)):
            if int(i) < int(quantity):
                print views[index] + ', cost(' + str(value) + ')'
            i += 1

def generarReescRW(numeros, stdin, lenQuery, query, vistas, type, quantity, costFile):
    infile = stdin
    modelos = []
    n = len(numeros)

    answerViews = {}

    i = 0
    for x in infile:
        l = x.strip().split()
        if l[0] != 'main:':
            answerViews[i] = str(crearReescritura(obtModeloRW(numeros, n, l, lenQuery, vistas), query))
            i += 1

    viewCosts(answerViews, type, quantity, costFile)
    return modelos

def obtModeloRW(numeros, n, lista, lenQuery, vistas):
    modp = []
    mod = []
    initeo = 0
    for var in lista:
        var2 = int(var)
        if var2 > (initeo + n):
            mcd = crearMCD(mod, vistas)
            if mcd != None:
                modp.append(mcd)
            mod = []
            initeo=initeo + n
        mod.append(numeros[var2-initeo])
    mcd = crearMCD(mod, vistas)
    if mcd != None:
        modp.append(mcd)
    return modp


def generarReescMCD(numeros, stdin, vistas):
    infile = stdin
    modelos = []
    count = 0
    x = infile.readline()
    x = infile.readline()
    while 1:
        if not(x):
            break
        x = infile.readline()
        l = x.strip().split()
        n = len(l)
        if n > 1: 
            mod = obtModelo(numeros, l, n)
            mcd = crearMCD(mod, vistas)
            if mcd != None:
                #print mod
                print mcd


def obtModelo(numeros, lista, n):
    mod = []
    for x in xrange(n):
        var = lista[x]
        mod.append(numeros[int(var)])
    return mod
