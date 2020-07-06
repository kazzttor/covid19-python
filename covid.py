#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# encoding=utf8

from argparse import ArgumentParser
from datetime import datetime, date, time, timedelta
import sqlite3
from sqlite3 import Error
db_file = 'covid.db3'
try:
        conex = sqlite3.connect(db_file)
        print("Versão do sqlite: ", sqlite3.version)
except Error as e:
        print(e)

conex.text_factory = str
cur = conex.cursor()

parser = ArgumentParser(description='Sistema de acompanhamento da Covid-19.',epilog='Observe as mensagens após a execução em caso de erros.')
parser.add_argument("-i", "--inicializa", help="inicializa banco de dados sqlite (elimina dados existentes).", action='store_true')
parser.add_argument("-n", "--novolocal", help="cadastra um novo local.", action='store_true')
parser.add_argument("-v", "--novodistrito", help="<id do local> cadastra uma nova região para um local existente.", action='store')
parser.add_argument("-r", "--registra", help="<id do local> cadastra os dados do balanço para uma cidade existente.", action='store')
parser.add_argument("-b", "--balanco", help="<id do local> exibe os dados do balanço para uma cidade existente.", action='store')
args = parser.parse_args()

hoje = datetime.now().strftime("%Y-%m-%d")

def executacomando(conn, comando):
    try:
        c = conn.cursor()
        c.execute(comando)
    except Error as e:
        print(e)
        
def validadata(data):
    try:
        datetime.strptime(data, "%Y-%m-%d")
        datao = datetime.strptime(data, "%Y-%m-%d")
        if datetime.now() > datao:
            return True
        else: 
            return False
    except ValueError:
        return False

def validanumero(numero):
    try:
        int(numero)
        return True
    except ValueError:
        return False
        
def diaanterior(data):
    diaanterior = datetime.strptime(data,"%Y-%m-%d") - timedelta(days=1)
    return diaanterior.strftime("%Y-%m-%d")
    
        
def regcaso(data,iddistrito):
    ontem = diaanterior(data)
    sqldiant = "SELECT idbalanco FROM balancos WHERE iddistrito = ? AND data = ?"
    diario = None
    gda = cur.execute(sqldiant,(iddistrito,ontem,))
    for rda in gda:
        diario = rda[0]
    if diario:
        regdia = 'S'
        regmsg = " (registro diário)"
    else:
        regdia = 'N'
        regmsg = None
    
    sqlgid = "SELECT iddistrito, nomedistrito FROM distritos WHERE iddistrito = ?"
    gid = cur.execute(sqlgid,(iddistrito,))
    distnum = None
    for ida in gid:
        distnum = ida[0]
        nomedist = ida[1]
    if distnum:
        totalcasos = 0
        totalmortes = 0
        sqlconc = "SELECT sum(novoscasos), sum(novasmortes) FROM balancos WHERE iddistrito = ? GROUP BY iddistrito"
        gcon = cur.execute(sqlconc,(distnum,))
        for concas in gcon:
            totalcasos = int(concas[0])
            totalmortes = int(concas[1])
        print("Data atual: ", data)
        print("Distrito atual: ", nomedist)
        casosap = (input("TOTAL DE CASOS DO DIA: Quantos casos o distrito tem até hoje? (padrão quantidade atual de casos: %s) " % (totalcasos)) or totalcasos)
        while not validanumero(casosap):
            print("Informação inválida. Um número deve ser fornecido.")
            casosap = (input("TOTAL DE CASOS DO DIA: Quantos casos o distrito tem até hoje? (padrão quantidade atual de casos: %s) " % (totalcasos)) or totalcasos)
        casosapurados = int(casosap)
        mortosap = (input("TOTAL DE MORTOS DO DIA: Quantos mortos o distrito tem até hoje? (padrão quantidade atual de mortes: %s) " % (totalmortes)) or totalmortes)
        while not validanumero(mortosap):
            print("Informação inválida. Um número deve ser fornecido.")
            mortosap = (input("TOTAL DE MORTOS DO DIA: Quantos mortos o distrito tem até hoje? (padrão quantidade atual de mortes: %s) " % (totalmortes)) or totalmortes)
        mortosapurados = int(mortosap)
        novoscasos = casosapurados - totalcasos
        novasmortes = mortosapurados - totalmortes
        if totalcasos != 0:
            txcc = (casosapurados/totalcasos) - 1
        else:
            txcc = 1
        if totalmortes != 0:
            txcm = (mortosapurados/totalmortes) - 1
        else:
            txcm = 1
            
        txlet = mortosapurados/casosapurados
        print("Confira os dados: \n\tDistrito: %s\n\tData: %s\n\tNovos casos: %s\n\tNovasmortes: %s\n\tÍndice de crescimento de casos: %s\n\tÍndice de crescimento de mortos: %s\n\tTaxa de letalidade: %s\n\t%s" % (nomedist, data, novoscasos, novasmortes, txcc, txcm, txlet, regmsg))
        sqlrc = "INSERT INTO balancos (iddistrito, data, novoscasos, novasmortes, aumentocasos, aumentomortes, txletalidade, registrodiario) VALUES (?,?,?,?,?,?,?,?)"
        confirmc = None
        while confirmc not in ("s", "n"):
            confirmc = input("Confirma? (s/n) ").lower()
            if confirmc == "s":
                cur.execute(sqlrc, (distnum,data,novoscasos,novasmortes,txcc,txcm,txlet,regdia))
                print(cur.lastrowid)
                conex.commit()
                print("Dados registrados.")
            elif confirmc == "n":
                print("Dados não cadastrados.")
            else:
                print("Resposta inválida. Responda s para sim, ou n para não")
        
    else: 
        print("Distrito inexistente ou inválido.")
    pass

def consolidacaso(data,idlocal):
    #Consolida as informações do dia.
    sqldistpai = "SELECT iddistrito FROM distritos WHERE registropai = ? AND iddistrito = ?"
    dips = 'S'
    gdist = cur.execute(sqldistpai,(dips,idlocal,))
    iddistpai = None
    for idrp in gdist:
        iddistpai = idrp[0]
    if iddistpai:
        sqlpopulacao = "SELECT populacao FROM locais WHERE idlocal = ?"
        sqlcontdia = "SELECT sum(novoscasos) AS totalcasos, sum(novasmortes) AS totalmortes FROM balancos INNER JOIN distritos ON distritos.iddistrito = balancos.iddistrito WHERE idlocal = ? AND data = ? AND registropai IS NULL GROUP BY idlocal"
        sqlconttot = "SELECT sum(novoscasos) AS totalcasos, sum(novasmortes) AS totalmortes FROM balancos INNER JOIN distritos ON distritos.iddistrito = balancos.iddistrito WHERE idlocal = ? AND registropai IS NULL GROUP BY idlocal"
        sqlrecup = "SELECT sum(novosrecuperados) AS totalrecuperados FROM balancos WHERE iddistrito = ? GROUP BY iddistrito"
        ontem = diaanterior(data)
        sqldiant = "SELECT idbalanco FROM balancos WHERE iddistrito = ? AND data = ?"
        diario = None
        gda = cur.execute(sqldiant,(iddistpai,ontem,))
        for rda in gda:
            diario = rda[0]
        if diario:
            regdia = 'S'
            regmsg = "(registro diário)"
        else:
            regdia = 'N'
            regmsg = "Sem registro ontem"
        gcd = cur.execute(sqlcontdia,(idlocal, data,))
        for rcd in gcd:
            casosdia = rcd[0]
            mortosdia = rcd[1]
        gct = cur.execute(sqlconttot,(idlocal,))
        for rct in gct:
            totalcasosc = rct[0]
            totalmortesc = rct[1]
        gcp = cur.execute(sqlpopulacao,(idlocal,))
        for rcp in gcp:
            populacao = rcp[0]
        gtr = cur.execute(sqlrecup,(iddistpai,))
        totalrecuperadosc = 0
        for rtr in gtr:
            totalrecuperadosc = rtr[0]

        if (totalcasosc-casosdia) != 0:
            txccc = (totalcasosc/(totalcasosc-casosdia)) -1
        else:
            txccc = 1
        if (totalmortesc-mortosdia) != 0:
            txcmc = (totalmortesc/(totalmortesc-mortosdia)) - 1
        else:
            txcmc = 1
        txletc = totalmortesc/totalcasosc
        txinc = (totalcasosc/float(populacao))*100000
        recuperadosap = (input("TOTAL PACIENTES RECUPERADOS: Quantos recuperados o distrito tem até hoje? (padrão quantidade atual de recuperados: %s) " % (totalrecuperadosc)) or totalrecuperadosc)
        while not validanumero(recuperadosap):
            print("Informação inválida. Um número deve ser fornecido.")
            recuperadosap = (input("TOTAL PACIENTES RECUPERADOS: Quantos recuperados o distrito tem até hoje? (padrão quantidade atual de recuperados: %s) " % (totalrecuperadosc)) or totalrecuperadosc)
        recuperadosapurados = int(recuperadosap)
        recuperadosdia = recuperadosapurados - totalrecuperadosc
        if totalrecuperadosc != 0:
            txcrc = (recuperadosapurados/totalrecuperadosc) -1
        else:
            txcrc = 1
        txrecupc = recuperadosapurados/totalcasosc
        txoclcap = (input("TAXA DE OCUPAÇÃO DE LEITOS: Qual a taxa em valor percentual (16.5 para 16,5%) de leitos ocupados? (opcional) ") or 0)
        txoclc = float(txoclcap)/100
        txocutcap = (input("TAXA DE OCUPAÇÃO DE UTI: Qual a taxa em valor percentual (16.5 para 16,5%) de leitos ocupados de UTI? (opcional) ") or 0)
        txocutc = float(txocutcap)/100
        txisocap = (input("TAXA DE ISOLAMENTO: Qual a taxa em valor percentual (16.5 para 16,5%) de o isolamento da população? (opcional) ") or 0)
        txisoc = float(txisocap)/100
        print("Verifique os dados:")
        print("CASOS:\tTotais: %s\tNesta data: %s\tAumento: %s \tIncidência: %s " % (totalcasosc, casosdia, txccc, txinc))
        print("MORTOS:\tTotais: %s\tNesta data: %s\tAumento: %s \tLetalidade %s " % (totalmortesc, mortosdia, txcmc, txletc))
        print("RECUPERADOS:\tTotais: %s\tNesta data: %s\tAumento: %s \tÍndice %s " % (recuperadosapurados, recuperadosdia, txcrc, txrecupc))
        print("OUTROS DADOS:\tTaxa de ocupação: %s\tTaxa de UTI: %s\tTaxa de Isolamento: %s " % (txoclc, txocutc, txisoc))
        sqlrcc = "INSERT INTO balancos (iddistrito, data, novoscasos, novasmortes, aumentocasos, aumentomortes, registrodiario, txletalidade, novosrecuperados, aumentorecuperados, txocupacao, txuti, txisolamento, txincidencia, txrecuperados) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        confirmco = None
        while confirmco not in ("s", "n"):
            confirmco = input("Confirma? (s/n) ").lower()
            if confirmco == "s":
                cur.execute(sqlrcc, (iddistpai,data,casosdia,mortosdia,txccc,txcmc,regdia,txletc,recuperadosdia,txcrc,txoclc,txocutc,txisoc,txinc,txrecupc))
                print(cur.lastrowid)
                conex.commit()
                print("Dados registrados.")
            elif confirmco == "n":
                print("Dados não cadastrados.")
            else:
                print("Resposta inválida. Responda s para sim, ou n para não")
    else:
        print("ERRO! Não localizado distrito-pai relacionado ao local escolhido. Base de dados com inconsistência.")
    pass

def inicializa():
    print("=== Inicializar o Banco de dados ====\nSe deseja reiniciar a coleta de dados, informações inconsistentes, ou banco de dados com erros, inicialize o banco de dados.\nATENÇÃO! Esta opção irá reinicializar o banco de dados apagando todos os dados existentes!\n\nEssa operação não poderá ser desfeita.")
    confirma = None
    while confirma not in ("s", "n"):
        confirma = input("Tem certeza? Confirma a reinicialização do Banco de Dados? (s/n) ").lower()
        if confirma == "s":
            sqld1 = """ DROP TABLE IF EXISTS balancos; """
            sqld2 = """ DROP TABLE IF EXISTS distritos; """
            sqld3 = """ DROP TABLE IF EXISTS locais; """
            sqlc1 = """ CREATE TABLE IF NOT EXISTS locais (
                                    idlocal integer PRIMARY KEY,
                                    nomelocal text NOT NULL,
                                    populacao integer NOT NULL,
                                    tipolocal text(1),                                  
                                    datainicio text(10)
                                ); """
            sqlc2 = """CREATE TABLE IF NOT EXISTS distritos (
                                    iddistrito integer PRIMARY KEY,
                                    idlocal integer NOT NULL,
                                    nomedistrito text NOT NULL,
                                    tipodistrito text(1) NOT NULL, 
                                    datainicio text(10) NOT NULL,
                                    macrodistrito text,
                                    registropai text(1),
                                    FOREIGN KEY (idlocal) REFERENCES locais (idlocal)
                                );"""
            sqlc3 = """CREATE TABLE IF NOT EXISTS balancos (
                                    idbalanco integer PRIMARY KEY,                                    
                                    iddistrito integer,
                                    data text(10) NOT NULL,
                                    novoscasos integer NOT NULL,                                    
                                    novasmortes integer NOT NULL,
                                    novosrecuperados integer,
                                    aumentocasos real, 
                                    aumentomortes real,
                                    aumentorecuperados real, 
                                    registrodiario text(1),
                                    txocupacao real,
                                    txuti real,
                                    txisolamento real,
                                    txincidencia real,
                                    txletalidade real,
                                    txrecuperados real,
                                    FOREIGN KEY (iddistrito) REFERENCES distritos (iddistrito)
                                );"""
            executacomando(conex, sqld1)
            executacomando(conex, sqld2)
            executacomando(conex, sqld3)
            executacomando(conex, sqlc1)
            executacomando(conex, sqlc2)
            executacomando(conex, sqlc3)         
            print("Banco de dados inicializado.")
        elif confirma == "n":
            print("Banco de dados não inicalizado.")
        else:
            print("Opção inválida.")     
    pass

def novolocal():
    print("== Cadastro de novo local ==\n\nVamos cadastrar um novo local.\nPode cadastrar quantos quiser e será usado para um balanço geral.\nPara cadastrar é preciso responder a algumas perguntas, como o nome do local, população, tipo de local, e a data do início das observações.")
    nomelocal = input("Digite o nome do novo local: ")
    hoje = datetime.now().strftime("%Y-%m-%d")
    populacao = int(input("Digite a população deste local (apenas números): "))
    tipos = ['C','E','P','N','M','O']
    tiposnome = {
        "C": "Cidade",
        "E": "Estado",
        "P": "País",
        "N": "Continente",
        "M": "Mundo",
        "O": "Outro",
    }
    print("Escolha o tipo de local:\n\tC - para cidade\n\tE - para estado\n\tP - para país\n\tN - para continente\n\tC - para mundo\n\tO - para outro")
    tipolocal = input("Digite a letra correspondente ao tipo do novo local: ").upper()
    while tipolocal not in tipos:
        print("Informação inválida: digite novamente.\nEscolha o tipo de local:\n\tC - para cidade\n\tE - para estado\n\tP - para país\n\tN - para continente\n\tC - para mundo\n\tO - para outro")
        tipolocal = input("Digite a letra correspondente ao tipo do novo local: ").upper()
    datainicio = (input("Digite da data de início das medições (formato %s - padrão data atual): " % (hoje)) or hoje)
    while not validadata(datainicio):
        print("Data informada inválida.")
        datainicio = (input("Digite da data de início das medições (formato %s - padrão data atual): " % (hoje)) or hoje)
    
    print("Verifique os dados:")
    print("Nome do local: %s" % (nomelocal))
    print("População: %s" % (populacao))
    print("Tipo: %s - %s" % (tipolocal, tiposnome[tipolocal]))
    print("Data de início das medições : %s" % (datainicio))
    cadastra = None
    while cadastra not in ("s", "n"):
        cadastra = input("Está tudo certo? Confirma? (s/n) ").lower()
        if cadastra == "s":
            sqlcl = "INSERT INTO locais (nomelocal,populacao,tipolocal,datainicio) VALUES (?,?,?,?)"
            cur.execute(sqlcl, (nomelocal,populacao,tipolocal,datainicio))
            print(cur.lastrowid)
            idl = cur.lastrowid
            sqlcl = "INSERT INTO distritos (idlocal,nomedistrito,tipodistrito,datainicio,registropai) VALUES (?,?,?,?,?)"
            regsitropais = 'S'
            cur.execute(sqlcl, (idl,nomelocal,tipolocal,datainicio,regsitropais))
            print(cur.lastrowid)
            conex.commit()
            print("Local cadastrado.")
        elif cadastra == "n":
            print("Local não cadastrado.\nPara cadastrar, realize novamente a opção de cadastramento com covid.py -n")
        else:
            print("Resposta inválida. Responda s para sim, ou n para não")
    pass

def novodistrito(idlocal):
    sqlgid = "SELECT idlocal, nomelocal, datainicio FROM locais WHERE idlocal = ?"
    gid = cur.execute(sqlgid,(idlocal,))
    idloc = None
    
    for ida in gid:
        idloc = ida[0]
        nomelocal = ida[1]
        datainicio = ida[2]
    
    if idloc:
        print("== Cadastro de novo distrito ==\n\nVamos cadastrar um novo distrito, que é uma subdivisão de um local já cadastrado.\nPode cadastrar quantos quiser e será usado para um balanço específico.\nPara cadastrar é preciso responder a algumas perguntas, como o nome do distrito, população, tipo de local, e a data do início das observações.")
        print("Cadastrando novo distrito para o seguinte local: ",nomelocal)
        nomedistrito = input("Digite o nome do novo distrito: ")
        tiposd = ['B','C','E','P','N','M','O']
        tiposdnome = {
            "B": "Bairro",
            "C": "Cidade",
            "E": "Estado",
            "P": "País",
            "N": "Continente",
            "M": "Mundo",
            "O": "Outro",
        }
        print("Escolha o tipo de distrito:\n\tB - para bairro\n\tC - para cidade\n\tE - para estado\n\tP - para país\n\tN - para continente\n\tC - para mundo\n\tO - para outro")
        tipodistrito = input("Digite a letra correspondente ao tipo do novo distrito: ").upper()        
        while tipodistrito not in tiposd:
            print("Informação inválida: digite novamente.\nEscolha o tipo de distrito:\n\tB - para bairro\n\tC - para cidade\n\tE - para estado\n\tP - para país\n\tN - para continente\n\tC - para mundo\n\tO - para outro")
            tipodistrito = input("Digite a letra correspondente ao tipo do novo distrito: ").upper()
        datainiciod = (input("Digite da data de início das medições (formato %s - padrão data inicio do local): " % (datainicio)) or datainicio)
        while not validadata(datainiciod):
            print("Data informada inválida.")
            datainiciod = (input("Digite da data de início das medições (formato %s - padrão data inicio do local): " % (datainicio)) or datainicio)
        macrodistrito = (input("Macrodistrito - é um nome de um agrupamento de distritos, geralmente em regiões vizinhas (opcional): ") or None)
        print("Verifique os dados:")
        print("Nome do distrito: %s" % (nomedistrito))
        print("Tipo: %s - %s" % (tipodistrito, tiposdnome[tipodistrito]))
        print("Data de início das medições : %s" % (datainiciod))
        if macrodistrito:
            print("Nome do macrodistrito: %s" % (macrodistrito))
        else:
            print("Sem macrodistrito atribuído.")
        cadastrad = None
        while cadastrad not in ("s", "n"):
            cadastrad = input("Está tudo certo? Confirma? (s/n) ").lower()
            if cadastrad == "s":
                sqlcd = "INSERT INTO distritos (idlocal,nomedistrito,tipodistrito,datainicio,macrodistrito) VALUES (?,?,?,?,?)"
                cur.execute(sqlcd, (idloc,nomedistrito,tipodistrito,datainiciod,macrodistrito))
                print(cur.lastrowid)
                conex.commit()
                print("Distrito cadastrado.")
            elif cadastrad == "n":
                print("Distrito não cadastrado.\nPara cadastrar, realize novamente a opção de cadastramento com covid.py -v <id do local>")
            else:
                print("Resposta inválida. Responda s para sim, ou n para não")
        
    else:
        print("Local inexistente ou inválido.")
    
    pass

def registra(idlocal):
    sqlgid = "SELECT idlocal, nomelocal FROM locais WHERE idlocal = ?"
    gid = cur.execute(sqlgid,(idlocal,))
    idloc = None
    hoje = datetime.now().strftime("%Y-%m-%d")
    for ida in gid:
        idloc = ida[0]
        nomelocal = ida[1]
    
    if idloc:
        print("== Registro de dados ==\n\nVamos cadastrar os dados para o local, informando os dados por distrito.")
        print("Cadastrando dados para o seguinte local: ",nomelocal)
        dataobs = (input("Digite a data da medição (formato %s  - padrão data atual): " % hoje) or hoje)
        while not validadata(dataobs):
            print("Data informada inválida.")
            dataobs = (input("Digite a data da medição (formato %s  - padrão data atual): " % hoje) or hoje)
        sqldist = "SELECT iddistrito, nomedistrito FROM distritos WHERE idlocal = ? AND registropai IS NULL"
        distritos = cur.execute(sqldist,(idlocal,))
        distg = distritos.fetchall()
        for distid in distg:
            print("Registro para o distrito %s" % (distid[1]))
            regcaso(dataobs,distid[0])
        
        consolidacaso(dataobs,idloc)
    else:
        print("Local inexistente ou inválido.")
        
    pass

def balanco(idlocal):
    sqlgid = "SELECT idlocal, nomelocal FROM locais WHERE idlocal = ?"
    gid = cur.execute(sqlgid,(idlocal,))
    idloc = None
    
    for ida in gid:
        idloc = ida[0]
        nomelocal = ida[1]
    
    if idloc:
        print("== Exibição do balanço ==\n\nVamos cadastrar um novo distrito, que é uma subdivisão de um local já cadastrado.\nPode cadastrar quantos quiser e será usado para um balanço específico.\nPara cadastrar é preciso responder a algumas perguntas, como o nome do distrito, população, tipo de local, e a data do início das observações.")
        print("Cadastrando novo distrito para o seguinte local: ",nomelocal)
    else:
        print("Local inexistente ou inválido.")
    
    # Query para média movel a calcular: SELECT data, novoscasos, novasmortes, novosrecuperados, txocupacao, txuti, txisolamento FROM balancos WHERE iddistrito = 1 ORDER BY data DESC LIMIT 5
    # Query para os distritos: SELECT balancos.iddistrito, sum(novoscasos) as totalcasos, sum(novasmortes) as totalmortes, aumentocasos, aumentomortes, txletalidade FROM balancos INNER JOIN distritos ON distritos.iddistrito = balancos.iddistrito WHERE data = '2020-06-30' AND registropai IS NULL GROUP BY balancos.iddistrito


    pass

    
if args.inicializa:
	inicializa()
 
if args.novolocal:
	novolocal()
    
if args.novodistrito:
	novodistrito(args.novodistrito)
    
if args.registra:
	registra(args.registra)
    
if args.balanco:
	balanco(args.balanco)