#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# encoding=utf8

from argparse import ArgumentParser
from datetime import datetime, date, time, timedelta
import locale
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
import sqlite3
from sqlite3 import Error
import sys
db_file = 'covid.db'
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
parser.add_argument("-v", "--novodistrito", type=int, metavar="idlocal", help="cadastra uma nova região para um local existente.", action='store')
parser.add_argument("-r", "--registra", type=int, metavar="idlocal", help="cadastra os dados do balanço para uma cidade existente.", action='store')
parser.add_argument("-b", "--balanco", type=int, metavar="idlocal", help="exibe os dados do balanço para uma cidade existente.", action='store')
parser.add_argument("-x", "--exclui", type=int, metavar="idlocal", help="exclui os dados do balanço para uma cidade existente.", action='store')
parser.add_argument("-d", "--data", type=str, metavar="data", help="(opera com as opções -b e -r) define a data de referência. Omitido -b assume a data atual, -r será solicitado. ", action='store')
# parser.add_argument("-w", "--web", help="gera o relatório no formato html.", action='store_true')
# parser.add_argument("-p", "--publicar", help="publicar relatório no formato html.", action='store_true')
parser.add_argument("--uti", type=float, metavar="taxadeuti", help="registra somente a taxa de uti para o local (requer -r e a data deve estar registrada).", nargs='?', const='pedir')
parser.add_argument("--isolamento", type=float, metavar="taxadeisolamento", help="registra somente a taxa de uti para o local (requer -r e a data deve estar registrada).", nargs='?', const='pedir')
parser.add_argument("--ocupacao", type=float, metavar="taxadeocupacao", help="registra somente a taxa de ocupação de leitos para o local (requer -r e a data deve estar registrada).", nargs='?', const='pedir')
parser.add_argument("--vacinacao", type=int, metavar=("Vacinados1dose","Vacinados2dose"), help="registra somente a quantidade de pessoas vacinadas para o local (requer -r e -d definidos e é exigido dois valores: vacinados da 1ª dose e da 2ª dose).", nargs=2, action='store')
args = parser.parse_args()

hoje = datetime.now().strftime("%Y-%m-%d")

def nomedistrito(iddistrito):
    sqldistrito = "SELECT nomedistrito FROM distritos WHERE iddistrito = ?"
    cur.execute(sqldistrito,(iddistrito,))
    distrito = cur.fetchone()
    return distrito[0]

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
        float(numero)
        return True
    except TypeError:
        return False
    except ValueError:
        return False
        
def diaanterior(data, dias=1):
    diaanterior = datetime.strptime(data,"%Y-%m-%d") - timedelta(days=dias)
    return diaanterior.strftime("%Y-%m-%d")

def statusav(valor):
    if valor > 0.15:
        return "Aumento"
    elif valor < -0.15:
        return "Queda"
    else:
        return "Estável"
    
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
        mortosap = (input("TOTAL DE ÓBITOS DO DIA: Quantos óbitos o distrito tem até hoje? (padrão quantidade atual de óbitos: %s) " % (totalmortes)) or totalmortes)
        while not validanumero(mortosap):
            print("Informação inválida. Um número deve ser fornecido.")
            mortosap = (input("TOTAL DE ÓBITOS DO DIA: Quantos óbitos o distrito tem até hoje? (padrão quantidade atual de óbitos: %s) " % (totalmortes)) or totalmortes)
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
        print("Confira os dados: \n\tDistrito: %s\n\tData: %s\n\tNovos casos: %s\n\tNovos Óbitos: %s\n\tÍndice de crescimento de casos: %s\n\tÍndice de crescimento de óbitos: %s\n\tTaxa de letalidade: %s\n\t%s" % (nomedist, data, novoscasos, novasmortes, txcc, txcm, txlet, regmsg))
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

def buscadistritopai(iddistrito):
    sqldistpai = "SELECT iddistrito FROM distritos WHERE registropai = ? AND iddistrito = ?"
    dips = 'S'
    gdist = cur.execute(sqldistpai,(dips,iddistrito,))
    distritopai = None
    for idrp in gdist:
        distritopai = idrp[0]
    return distritopai

def consolidacaso(data,idlocal):
    iddistpai = buscadistritopai(idlocal)
    if iddistpai:
        sqlpopulacao = "SELECT populacao FROM locais WHERE idlocal = ?"
        sqlcontdia = "SELECT sum(novoscasos) AS totalcasos, sum(novasmortes) AS totalmortes FROM balancos INNER JOIN distritos ON distritos.iddistrito = balancos.iddistrito WHERE idlocal = ? AND data = ? AND registropai IS NULL GROUP BY idlocal"
        sqlconttot = "SELECT sum(novoscasos) AS totalcasos, sum(novasmortes) AS totalmortes FROM balancos INNER JOIN distritos ON distritos.iddistrito = balancos.iddistrito WHERE idlocal = ? AND registropai IS NULL GROUP BY idlocal"
        sqlrecup = "SELECT sum(novosrecuperados) AS totalrecuperados, sum(vacinadose1) as vacinados1, sum(vacinadose2) as vacinados2 FROM balancos WHERE iddistrito = ? GROUP BY iddistrito"
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
        totalrecuperadosc = totalvacinados1 = totalvacinados2 = 0
        for rtr in gtr:
            totalrecuperadosc = rtr[0]
            totalvacinados1c = rtr[1]
            totalvacinados2c = rtr[2]

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
        recuperadosap = (input("TOTAL PACIENTES RECUPERADOS: Quantos recuperados o local tem até hoje? (padrão quantidade atual de recuperados: %s) " % (totalrecuperadosc)) or totalrecuperadosc)
        while not validanumero(recuperadosap):
            print("Informação inválida. Um número deve ser fornecido.")
            recuperadosap = (input("TOTAL PACIENTES RECUPERADOS: Quantos recuperados o local tem até hoje? (padrão quantidade atual de recuperados: %s) " % (totalrecuperadosc)) or totalrecuperadosc)
        recuperadosapurados = int(recuperadosap)
        recuperadosdia = recuperadosapurados - totalrecuperadosc
        if totalrecuperadosc != 0:
            txcrc = (recuperadosapurados/totalrecuperadosc) -1
        else:
            txcrc = 1
        txrecupc = recuperadosapurados/totalcasosc
        vacinados1ap = (input("TOTAL PESSOAS VACINADAS (1ª DOSE): Quantos pessoas vacinadas? (padrão quantidade atual de vacinados (1ª dose): %s) " % (totalvacinados1c)) or totalvacinados1c)
        while not validanumero(vacinados1ap):
            print("Informação inválida. Um número deve ser fornecido.")
            recuperadosap = (input("TOTAL PESSOAS VACINADAS (1ª DOSE): Quantos pessoas vacinadas? (padrão quantidade atual de vacinados (1ª dose): %s) " % (totalvacinados1c)) or totalvacinados1c)
        vacinados1apurados = int(vacinados1ap)
        vacinados1dia = vacinados1apurados - totalvacinados1c
        vacinados2ap = (input("TOTAL PESSOAS VACINADAS (2ª DOSE): Quantos pessoas vacinadas? (padrão quantidade atual de vacinados (2ª dose): %s) " % (totalvacinados2c)) or totalvacinados2c)
        while not validanumero(vacinados2ap):
            print("Informação inválida. Um número deve ser fornecido.")
            recuperadosap = (input("TOTAL PESSOAS VACINADAS (2ª DOSE): Quantos pessoas vacinadas? (padrão quantidade atual de vacinados (2ª dose): %s) " % (totalvacinados2c)) or totalvacinados2c)
        vacinados2apurados = int(vacinados2ap)
        vacinados2dia = vacinados2apurados - totalvacinados2c
        txoclcap = (input("TAXA DE OCUPAÇÃO DE LEITOS: Qual a taxa em valor percentual (16.5 para 16,5%) de leitos ocupados? (opcional) ") or 0)
        txoclc = float(txoclcap)/100
        txocutcap = (input("TAXA DE OCUPAÇÃO DE UTI: Qual a taxa em valor percentual (16.5 para 16,5%) de leitos ocupados de UTI? (opcional) ") or 0)
        txocutc = float(txocutcap)/100
        txisocap = (input("TAXA DE ISOLAMENTO: Qual a taxa em valor percentual (16.5 para 16,5%) de o isolamento da população? (opcional) ") or 0)
        txisoc = float(txisocap)/100
        print("Verifique os dados:")
        print("CASOS:\tTotais: %s\tNesta data: %s\tAumento: %s \tIncidência: %s " % (totalcasosc, casosdia, txccc, txinc))
        print("ÓBITOS:\tTotais: %s\tNesta data: %s\tAumento: %s \tLetalidade %s " % (totalmortesc, mortosdia, txcmc, txletc))
        print("RECUPERADOS:\tTotais: %s\tNesta data: %s\tAumento: %s \tÍndice %s " % (recuperadosapurados, recuperadosdia, txcrc, txrecupc))
        print("VACINADOS: \t1ª dose: %s\t1ª dose nesta data: %s\t2ª dose: %s\t2ª dose nesta data: %s" % (vacinados1apurados,vacinados1dia,vacinados2apurados,vacinados2dia))
        print("OUTROS DADOS:\tTaxa de ocupação: %s\tTaxa de UTI: %s\tTaxa de Isolamento: %s " % (txoclc, txocutc, txisoc))
        sqlrcc = "INSERT INTO balancos (iddistrito, data, novoscasos, novasmortes, aumentocasos, aumentomortes, registrodiario, txletalidade, novosrecuperados, aumentorecuperados, txocupacao, txuti, txisolamento, txincidencia, txrecuperados, vacinadose1, vacinadose2) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        confirmco = None
        while confirmco not in ("s", "n"):
            confirmco = input("Confirma? (s/n) ").lower()
            if confirmco == "s":
                cur.execute(sqlrcc, (iddistpai,data,casosdia,mortosdia,txccc,txcmc,regdia,txletc,recuperadosdia,txcrc,txoclc,txocutc,txisoc,txinc,txrecupc,vacinados1dia,vacinados2dia))
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
                                    vacinadose1 integer,
                                    vacinadose2 integer,
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

def registra(idlocal, data="pedir"):
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
        if data == "pedir" or validadata(data) is False: 
            dataobs = (input("Digite a data da medição (formato %s  - padrão data atual): " % hoje) or hoje)
            while not validadata(dataobs):
                print("Data informada inválida.")
                dataobs = (input("Digite a data da medição (formato %s  - padrão data atual): " % hoje) or hoje)
        else:
            dataobs = data
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

def mediamovel(iddistrito,dataref):
    sqlmm = "SELECT data, novoscasos, novasmortes, novosrecuperados, txocupacao, txuti, txisolamento, txletalidade, vacinadose1, vacinadose2 FROM balancos WHERE iddistrito = ?  AND data < ? ORDER BY data DESC LIMIT 7"
    dadosmm = cur.execute(sqlmm,(iddistrito,dataref,))
    tdmm = dadosmm.fetchall()
    casos = mortes = recuperados = vacinados1 = vacinados2 = 0
    tocp = tuti = tiso = tlet = 0.0
    for numdt in tdmm:
        if numdt[1]: 
            casos = casos + int(numdt[1])
        if numdt[2]: 
            mortes = mortes + int(numdt[2])
        if numdt[3]: 
            recuperados = recuperados + int(numdt[3])
        if numdt[4]: 
            tocp = tocp + float(numdt[4])
        if numdt[5]: 
            tuti = tuti + float(numdt[5])
        if numdt[6]: 
            tiso = tiso + float(numdt[6])
        if numdt[7]: 
            tlet = tlet + float(numdt[7])
        if numdt[8]:
            vacinados1 = vacinados1 + int(numdt[8])
        if numdt[9]:
            vacinados2 = vacinados2 + int(numdt[9])        
        
    d = dict();
    d['casos'] = casos/7.0
    d['mortes'] = mortes/7.0
    d['recuperados'] = recuperados/7.0
    d['txocupacao'] = tocp/7
    d['txuti'] = tuti/7
    d['txisolamento'] = tiso/7
    d['txletalidade'] = tlet/7
    d['vacina1'] = vacinados1/7.0
    d['vacina2'] = vacinados2/7.0
    return d


def txcrescimento(iddistrito,dataref,dias):
    if int(dias) == 1:
        offsetd = "-1 day"
    else:
        offsetd = "-" + str(dias) + " days"
    sqldz = "SELECT data, sum(novoscasos) AS totalcasos, sum(novasmortes) AS totalmortes, sum(novosrecuperados) AS totalrecuperados, sum(vacinadose1) as totalvacinados1, sum(vacinadose2) as totalvacinados2 FROM balancos WHERE iddistrito = ? AND data <= date(?,?) GROUP BY iddistrito"
    sqlda = "SELECT data, sum(novoscasos) AS totalcasos, sum(novasmortes) AS totalmortes, sum(novosrecuperados) AS totalrecuperados, sum(vacinadose1) as totalvacinados1, sum(vacinadose2) as totalvacinados2 FROM balancos WHERE iddistrito = ? AND data <= ? GROUP BY iddistrito"
    gdz = cur.execute(sqldz,(iddistrito,dataref,offsetd,))
    casoszero = morteszero = recuperadoszero = casosatual = mortesatual = recuperadosatual = vacinados1zero = vacinados2zero = vacinados1atual = vacinados2atual = 0
    for dtz in gdz:
        if dtz[1]:
            casoszero = float(dtz[1])
        if dtz[2]:
            morteszero = float(dtz[2])
        if dtz[3]:
            recuperadoszero = float(dtz[3])
        if dtz[4]:
            vacinados1zero = float(dtz[4])
        if dtz[5]:
            vacinados1zero = float(dtz[5])         
    gda = cur.execute(sqlda,(iddistrito,dataref,))
    for dta in gda:
        if dta[1]:
            casosatual = float(dta[1])
        if dta[2]:
            mortesatual = float(dta[2])
        if dta[3]:
            recuperadosatual = float(dta[3])
        if dta[4]:
            vacinados1atual = float(dta[4])
        if dta[5]:
            vacinados2atual = float(dta[5])        
    c = dict();
    c['aumentocasos'] = (casosatual/casoszero) - 1.0 if casoszero != 0 else 0
    c['aumentomortes'] = (mortesatual/morteszero) - 1.0 if morteszero != 0 else 0
    c['aumentorecuperados'] = (recuperadosatual/recuperadoszero) - 1.0 if recuperadoszero != 0 else 0
    c['aumentovacinados1'] = (vacinados1atual/vacinados1zero) - 1.0 if vacinados1zero != 0 else 0
    c['aumentovacinados2'] = (vacinados2atual/vacinados1zero) - 1.0 if vacinados2zero != 0 else 0
    return c

def exibeestatistica(iddist,data,web="n"):
    sqltotcasos = "SELECT sum(novoscasos) AS totalcasos, sum(novasmortes) AS totalmortes, sum(novosrecuperados) AS totalrecuperados, sum(vacinadose1) AS totalvacinados1, sum(vacinadose2) AS totalvacinados2 FROM balancos WHERE iddistrito = ? AND data <= ? GROUP BY iddistrito"
    cur.execute(sqltotcasos,(iddist,data,))
    gtc = cur.fetchone()
    try: 
        totalcasos = totalmortos = totalrecuperados = totalvacinados1 = totalvacinados2 = 0
        if validanumero(gtc[0]):
            totalcasos = int(gtc[0])
        if validanumero(gtc[1]):
            totalmortos = int(gtc[1])
        if validanumero(gtc[2]): 
            totalrecuperados = int(gtc[2])
        if validanumero(gtc[3]): 
            totalvacinados1 = int(gtc[3])
        if validanumero(gtc[4]): 
            totalvacinados2 = int(gtc[4])
        
        sqldadosdiae = "SELECT novoscasos, novasmortes, novosrecuperados, aumentocasos, aumentomortes, aumentorecuperados, registrodiario, txocupacao, txuti, txisolamento, txincidencia, txletalidade, txrecuperados, vacinadose1, vacinadose2 FROM balancos WHERE iddistrito = ? AND data = ?"
        cur.execute(sqldadosdiae,(iddist,data,))
        dcd = cur.fetchone()
        novoscasos = novasmortes = novosrecuperados = novosvacinados1 = novosvacinados2 = 0
        txa_casos = txa_mortes = txa_recuperados = tx_ocup = tx_uti = tx_isolam = tx_inc = tx_let = tx_recup = 0.0
        regsitrodiario = ""
        if validanumero(dcd[0]):
            novoscasos = dcd[0]
        if validanumero(dcd[1]):
            novasmortes = dcd[1]
        if validanumero(dcd[2]):
            novosrecuperados = dcd[2]
        if validanumero(dcd[3]):
            txa_casos = float(dcd[3])*100
        if validanumero(dcd[4]):
            txa_mortes = float(dcd[4])*100
        if validanumero(dcd[5]):
            txa_recuperados = float(dcd[5])*100
        if validanumero(dcd[6]):
            regsitrodiario = dcd[6]
        if validanumero(dcd[7]):
            tx_ocup = float(dcd[7])*100
        if validanumero(dcd[8]):
            tx_uti = float(dcd[8])*100
        if validanumero(dcd[9]):
            tx_isolam = float(dcd[9])*100
        if validanumero(dcd[10]):
            tx_inc = float(dcd[10])
        if validanumero(dcd[11]):
            tx_let = float(dcd[11])*100
        if validanumero(dcd[12]):
            tx_recup = float(dcd[12])*100
        if validanumero(dcd[13]):
            novosvacinados1 = dcd[13]
        if validanumero(dcd[14]):
            novosvacinados2 = dcd[14]             
        memovlocal = mediamovel(iddist,data)
        mm_casos = float(memovlocal['casos'])
        mm_mortos = float(memovlocal['mortes'])
        mm_recuperados = float(memovlocal['recuperados'])
        mm_txocupacao = float(memovlocal['txocupacao'])
        mm_txuti = float(memovlocal['txuti'])
        mm_txisolamento = float(memovlocal['txisolamento'])
        mm_letalidade = float(memovlocal['txletalidade'])
        mm_vacina1 = float(memovlocal['vacina1'])
        mm_vacina2 = float(memovlocal['vacina2'])
        memovlocal15 = mediamovel(iddist,diaanterior(data,15))
        # print(diaanterior(data,15))
        mm_casos15 = float(memovlocal15['casos'])
        mm_mortos15 = float(memovlocal15['mortes'])
        mm_recuperados15 = float(memovlocal15['recuperados'])
        mm_txisolamento15 = float(memovlocal15['txisolamento'])
        mm_vacina115 = float(memovlocal15['vacina1'])
        mm_vacina215 = float(memovlocal15['vacina2'])
        txcrsemloc = txcrescimento(iddist,data,7)
        au7d_casos = float(txcrsemloc['aumentocasos'])*100
        au7d_mortos = float(txcrsemloc['aumentomortes'])*100
        au7d_recuperados = float(txcrsemloc['aumentorecuperados'])*100
        au7d_vacinados1 = float(txcrsemloc['aumentovacinados1'])*100
        au7d_vacinados2 = float(txcrsemloc['aumentovacinados2'])*100
        txcrmesloc = txcrescimento(iddist,data,30)
        au30d_casos = float(txcrmesloc['aumentocasos'])*100
        au30d_mortos = float(txcrmesloc['aumentomortes'])*100
        au30d_recuperados = float(txcrmesloc['aumentorecuperados'])*100
        au30d_vacinados1 = float(txcrmesloc['aumentovacinados1'])*100
        au30d_vacinados2 = float(txcrmesloc['aumentovacinados2'])*100
        varmm_casos = (mm_casos/mm_casos15) - 1.0 if mm_casos15 != 0.0 else 0
        varmm_mortos = (mm_mortos/mm_mortos15) - 1.0 if mm_mortos15 != 0.0 else 0
        varmm_vacina1 = (mm_vacina1/mm_vacina115) - 1.0 if mm_vacina115 != 0.0 else 0
        varmm_vacina2 = (mm_vacina2/mm_vacina215) - 1.0 if mm_vacina215 != 0.0 else 0
        varmm_recuperados = (mm_recuperados/mm_recuperados15) - 1.0 if mm_recuperados15 != 0.0 else 0
        varmm_isolamento = (mm_txisolamento/mm_txisolamento15) - 1.0 if mm_txisolamento15 != 0.0 else 0
        if (web == "n"):
            print("CASOS:")
            msgcasos = ""
            msgcasos = msgcasos + '\tTotal: {:n}'.format(totalcasos)
            msgcasos = msgcasos + '\tNovos: {:n}'.format(novoscasos)
            msgcasos = msgcasos + '\n\tMédia móvel (7 registros anteriores): {:n}'.format(mm_casos) + ', 15 dias antes: {:n}'.format(mm_casos15) + ', Variação de casos: {:.2f}%'.format(varmm_casos*100) + ', Tendência: ' + statusav(varmm_casos)
            msgcasos = msgcasos + "\n\tAumento de casos: " + '{:.1n}% (ao balanço anterior)'.format(txa_casos)
            if au7d_casos:
                msgcasos = msgcasos + ' {:n}%  (em uma semana)'.format(au7d_casos)
            if au30d_casos:
                msgcasos = msgcasos + ' {:n}%  (em 30 dias)'.format(au30d_casos)
            print(msgcasos)
            print("ÓBITOS:")
            msgmortes = ""
            msgmortes = msgmortes + '\tTotal: {:n}'.format(totalmortos)
            msgmortes = msgmortes + '\tNovos: {:n}'.format(novasmortes)
            msgmortes = msgmortes + '\n\tMédia móvel (7 registros anteriores): {:n}'.format(mm_mortos) + ', 15 dias antes: {:n}'.format(mm_mortos15) + ', Variação de óbitos: {:.2f}%'.format(varmm_mortos*100) + ', Tendência: ' + statusav(varmm_mortos)
            msgmortes = msgmortes + '\n\tAumento de óbitos: {:.1n}% (ao balanço anterior)'.format(txa_mortes)
            if au7d_mortos:
                msgmortes = msgmortes + ' {:n}%  (em uma semana)'.format(au7d_mortos)
            if au30d_mortos:
                msgmortes = msgmortes + ' {:n}% (em 30 dias)'.format(au30d_mortos)
            print(msgmortes)
            if totalrecuperados:
                print("RECUPERADOS:")
                msgrecup = ""
                msgrecup = msgrecup + '\tTotal: {:n}'.format(totalrecuperados)
                msgrecup = msgrecup + '\tNovos: {:n}'.format(novosrecuperados)
                msgrecup = msgrecup + '\n\tMédia móvel (7 registros anteriores): {:n}'.format(mm_recuperados) + ', 15 dias antes: {:n}'.format(mm_recuperados15) + ', Variação de recuperados: {:.2f}%'.format(varmm_recuperados*100) + ', Tendência: ' + statusav(varmm_recuperados)
                msgrecup = msgrecup + '\n\tAumento de recuperados: {:.1n}% (ao balanço anterior)'.format(txa_recuperados)
                if au7d_recuperados:
                    msgrecup = msgrecup + ' {:n}%  (em uma semana)'.format(au7d_recuperados)
                if au30d_recuperados:
                    msgrecup = msgrecup + ' {:n}%  (em 30 dias)'.format(au30d_recuperados)
                print(msgrecup)
            if totalvacinados1 or totalvacinados2:
                print("VACINADOS:")
                totalvacinados = totalvacinados1 + totalvacinados2
                diaontem = diaanterior(data)
                totvacina = vacinados(iddist,diaontem)
                vacina1dant = vacina2dant = 0.000000000001
                if totvacina['dose1'] is not None:
                    vacina1dant = vacina1dant + totvacina['dose1']
                if totvacina['dose2'] is not None:
                    vacina2dant = vacina2dant + totvacina['dose1']
                txa_vacinados1 = (totalvacinados1/vacina1dant) - 1.0
                txa_vacinados2 = (totalvacinados2/vacina2dant) - 1.0          
                msgvac = ""
                msgvac = msgvac + '\tTotal: {:n} ({:n} com 1ª dose e {:n} com 2ª dose)'.format(totalvacinados, totalvacinados1, totalvacinados2)
                msgvac = msgvac + '\tNovos: 1ª dose {:n}, 2ª dose {:n}'.format(novosvacinados1, novosvacinados2)
                msgvac = msgvac + '\n\tProporção da população vacinada: ({:n}% com 1ª dose e {:n}% com 2ª dose)'.format(float(totvacina['txdose1'])*100, float(totvacina['txdose2'])*100)
                msgvac = msgvac + '\n\tMédia móvel 1ª dose (7 registros anteriores): {:n}'.format(mm_vacina1) + ', 15 dias antes: {:n}'.format(mm_vacina115) + ', Variação de vacinados (1ª dose): {:.2f}%'.format(varmm_vacina1*100) + ', Tendência: ' + statusav(varmm_vacina1)
                msgvac = msgvac + '\n\tMédia móvel 2ª dose (7 registros anteriores): {:n}'.format(mm_vacina2) + ', 15 dias antes: {:n}'.format(mm_vacina215) + ', Variação de vacinados (2ª dose): {:.2f}%'.format(varmm_vacina2*100) + ', Tendência: ' + statusav(varmm_vacina2)
                msgvac = msgvac + '\n\tAumento de vacinados: 1ª dose {:.1n}% (ao balanço anterior)'.format(txa_vacinados1)
                if au7d_vacinados1:
                    msgvac = msgvac + ' {:n}%  (em uma semana)'.format(au7d_vacinados1)
                if au30d_vacinados1:
                    msgvac = msgvac + ' {:n}%  (em 30 dias)'.format(au30d_vacinados1)
                msgvac = msgvac + '\n\tAumento de vacinados: 2ª dose {:.1n}% (ao balanço anterior)'.format(txa_vacinados2)
                if au7d_vacinados2:
                    msgvac = msgvac + ' {:n}%  (em uma semana)'.format(au7d_vacinados2)
                if au30d_vacinados2:
                    msgvac = msgvac + ' {:n}%  (em 30 dias)'.format(au30d_vacinados2)
                print(msgvac)
            print("Outros dados:")
            odata = ""
            if tx_let:
                odata = odata + '\tTaxa de letalidade: {:n}%'.format(float(tx_let))
            if tx_inc:
                odata = odata + '\tTaxa de incidência: {:n}/100.000 hab (1 caso a cada {:n} habitantes)'.format(float(tx_inc), int(1/(tx_inc/100000)))
            if tx_ocup:
                odata = odata + '\n\tTaxa de ocupação: {:n}%'.format(float(tx_ocup)) + ' (Média Movel - 7 dias: {:n}%)'.format(float(mm_txocupacao*100))
            if tx_uti:
                odata = odata + '\n\tTaxa de ocupação de UTI: {:n}%'.format(float(tx_uti)) + ' (Média Movel - 7 dias: {:n}%)'.format(float(mm_txuti*100))
            if tx_isolam:
                odata = odata + '\n\tTaxa de isolamento: {:n}%'.format(float(tx_isolam))
                odata = odata + '\tMédia móvel (7 registros anteriores): {:n}'.format(mm_txisolamento*100) + ', 15 dias antes: {:n}%'.format(mm_txisolamento15*100) + ', Variação da Taxa de Isolamento: {:.2f}%'.format(varmm_isolamento*100) + ', Tendência: ' + statusav(varmm_isolamento)
            if tx_recup:
                odata = odata + '\n\tÍndice de recuperados: {:n}%'.format(float(tx_recup))
                odata = odata + '\t(Casos Ativos: {:n})'.format((totalcasos-totalrecuperados))
            print(odata)
        else:
            esqueletoweb = ""
    except TypeError as e:
        sys.exit("Não localizados dados para essa data.")
    pass

def vacinados(iddist,data):
    sqlpoplocal = "SELECT populacao FROM locais WHERE idlocal = ?"
    cur.execute(sqlpoplocal, (iddist,))
    pop_data = cur.fetchone()
    populacao = pop_data[0]
    sqlvac = "SELECT SUM(vacinadose1), sum(vacinadose2) FROM balancos WHERE data <= ? AND iddistrito = ?"
    cur.execute(sqlvac, (data,iddist,))
    dadovacina = cur.fetchone()
    vacinado = dict();
    vacinado['dose1'] = vacinado['dose2'] = 0
    if dadovacina[0] is not None: 
        vacinado['dose1'] = dadovacina[0]
        vacinado['txdose1'] = dadovacina[0]/(populacao*1.0)
    if dadovacina[1] is not None: 
        vacinado['dose2'] = dadovacina[1]
        vacinado['txdose2'] = dadovacina[1]/(populacao*1.0)
    return vacinado

def updbalanco(dado,idlocal, data="pedir", valor="pedir"):
    dados = ["txocupacao","txuti","txisolamento","vacinadose1","vacinadose2"]
    if dado not in dados:
        dado = input("Digite o itpo de informação a ser atualizada (Valores possíveis: %s): " % dados)
        while dado not in dados:
            dado = input("Digite o itpo de informação a ser atualizada (Valores possíveis: %s): " % dados)
    titulodado = {
        "txocupacao": "Taxa de ocupação de leitos",
        "txuti": "Taxa de ocupação de leitos de UTI",
        "txisolamento": "Taxa de isolamento",
        "vacinadose1": "Número diário de vacinados (1ª dose)",
        "vacinadose2": "Número diário de vacinados (2ª dose)"
    }
    if data == "pedir" or validadata(data) is False: 
        dataobs = (input("Digite a data da medição (formato %s  - padrão data atual): " % hoje) or hoje)
        while not validadata(dataobs):
            print("Data informada inválida.")
            dataobs = (input("Digite a data da medição (formato %s  - padrão data atual): " % hoje) or hoje)
    else:
        dataobs = data
    sqlverifica = "SELECT count(idbalanco) FROM balancos WHERE data = ? AND iddistrito = ?"
    cur.execute(sqlverifica, (dataobs,idlocal,))
    registros = cur.fetchone()
    numregistros = registros[0]
    if numregistros > 0:
        if valor == "pedir" or validanumero(valor) is False:
            valorobs = int(input("Digite o valor de %s, onde separa-se inteiro e fração com ponto, caso necessário (16,7 como 16.7) Valor padrão 0: " % titulodado[dado]) or 0)
            while not validanumero(valorobs):
                print("Valor informado inválido.")
                valorobs = int(input("Digite o valor de %s, onde separa-se inteiro e fração com ponto, caso necessário (16,7 como 16.7) Valor padrão 0: " % titulodado[dado]) or 0)
        else:
            valorobs = int(valor)
        if dado in ["txocupacao","txuti","txisolamento"]:
            valorobs /= 100.0
        print("Confira os dados: \n\tDistrito: %s\n\tData: %s\n\t%s: %s" % (nomedistrito(idlocal), data, titulodado[dado], valorobs))
        sqlrc = "UPDATE balancos SET " + dado + " = ? WHERE iddistrito = ? AND data = ?"
        confirmc = None
        while confirmc not in ("s", "n"):
            confirmc = input("Confirma? (s/n) ").lower()
            if confirmc == "s":
                cur.execute(sqlrc, (valorobs,idlocal,data))
                print(cur.lastrowid)
                conex.commit()
                print("Dados atualizados.")
            elif confirmc == "n":
                print("Dados não atualizados.")
            else:
                print("Resposta inválida. Responda s para sim, ou n para não")
    else:
        print("Não foram registrados dados para a data.")

def balanco(idlocal,dataref=hoje):
    sqlgid = "SELECT idlocal, nomelocal FROM locais WHERE idlocal = ?"
    gid = cur.execute(sqlgid,(idlocal,))
    idloc = None
    
    for ida in gid:
        idloc = ida[0]
        nomelocal = ida[1]
    
    if idloc:
        print("== Exibição do balanço ==")
        data = datetime.strptime(dataref,"%Y-%m-%d")
        print("Data da observação: %s\tLocal: %s" % (data.strftime("%d/%m/%Y"),nomelocal))
        print("\nResumo para o local\n")
        iddip = buscadistritopai(idloc)
        exibeestatistica(iddip, dataref)
        sqldist = "SELECT iddistrito, nomedistrito FROM distritos WHERE idlocal = ? AND registropai IS NULL"
        distritos = cur.execute(sqldist,(idlocal,))
        distg = distritos.fetchall()
        print("\nBalanço por distrito:\n")
        for distid in distg:
            print("Balanço para o distrito %s" % (distid[1]))
            exibeestatistica(distid[0], dataref)

    else:
        print("Local inexistente ou inválido.")
    
    # Query para média movel a calcular: SELECT data, novoscasos, novasmortes, novosrecuperados, txocupacao, txuti, txisolamento FROM balancos WHERE iddistrito = 1  AND data < '2020-05-25' ORDER BY data DESC LIMIT 5
    # Query para os distritos: SELECT balancos.iddistrito, sum(novoscasos) as totalcasos, sum(novasmortes) as totalmortes, aumentocasos, aumentomortes, txletalidade FROM balancos INNER JOIN distritos ON distritos.iddistrito = balancos.iddistrito WHERE data = '2020-06-30' AND registropai IS NULL GROUP BY balancos.iddistrito


    pass

def excluibalanco(idlocal,dataref=hoje):
    sqlgid = "SELECT idlocal, nomelocal FROM locais WHERE idlocal = ?"
    gid = cur.execute(sqlgid,(idlocal,))
    idloc = None
    
    for ida in gid:
        idloc = ida[0]
        nomelocal = ida[1]
    
    if idloc:
        print("== Exclusão do balanço ==")
        data = datetime.strptime(dataref,"%Y-%m-%d")
        print("Data a ser excluída: %s\tLocal: %s" % (data.strftime("%d/%m/%Y"),nomelocal))
        sqldel = "DELETE FROM balancos WHERE iddistrito IN (SELECT iddistrito FROM distritos WHERE idlocal = ?) AND data = ?"
        cadastra = None
        while cadastra not in ("s", "n"):
            cadastra = input("Está tudo certo? Confirma? (s/n) ").lower()
            if cadastra == "s":        
                cur.execute(sqldel,(idloc,data.strftime("%Y-%m-%d")))
                registrosalterados = int(cur.rowcount)
                print("%d linhas excluídas." % (registrosalterados))
                conex.commit()
            elif cadastra == "n":
                print("Local não cadastrado.\nPara cadastrar, realize novamente a opção de cadastramento com covid.py -n")
            else:
                print("Resposta inválida. Responda s para sim, ou n para não")            
    else:
        print("Local inexistente ou inválido.")
    
    # Query para média movel a calcular: SELECT data, novoscasos, novasmortes, novosrecuperados, txocupacao, txuti, txisolamento FROM balancos WHERE iddistrito = 1  AND data < '2020-05-25' ORDER BY data DESC LIMIT 5
    # Query para os distritos: SELECT balancos.iddistrito, sum(novoscasos) as totalcasos, sum(novasmortes) as totalmortes, aumentocasos, aumentomortes, txletalidade FROM balancos INNER JOIN distritos ON distritos.iddistrito = balancos.iddistrito WHERE data = '2020-06-30' AND registropai IS NULL GROUP BY balancos.iddistrito


    pass
    
if args.inicializa:
	inicializa()
 
if args.novolocal:
	novolocal()
    
if args.novodistrito:
	novodistrito(args.novodistrito)
    
if args.registra:
    if args.data:
        if validadata(args.data):
            if (args.uti or args.isolamento or args.ocupacao or args.vacinacao):
                if (args.uti):
                    updbalanco("txuti",args.registra,args.data,args.uti)
                if (args.isolamento):
                    updbalanco("txisolamento",args.registra,args.data,args.isolamento)
                if (args.ocupacao):
                    updbalanco("txocupacao",args.registra,args.data,args.ocupacao)
                if (args.vacinacao):
                    vacinadose1ap = args.vacinacao[0]
                    vacinadose2ap = args.vacinacao[1]
                    diaontem = diaanterior(args.data)
                    totvacina = vacinados(args.registra,diaontem)
                    novosvacinados1 = vacinadose1ap - totvacina['dose1']
                    novosvacinados2 = vacinadose2ap - totvacina['dose2']
                    print("Confira os dados: \n\tVacinados 1ª dose: %s\tNovos: %s\n\tVacinados 2ª dose: %s\t\tNovos: %s\nSe os dados estiverem corretos, confirme cada um dos dados solicitados." % (vacinadose1ap,novosvacinados1,vacinadose2ap,novosvacinados2))
                    updbalanco("vacinadose1",args.registra,args.data,novosvacinados1)
                    updbalanco("vacinadose2",args.registra,args.data,novosvacinados2)
            else:
	            registra(args.registra,args.data)
        else:
            print("Data informada inválida: utilize uma dáta válida, no passado para a opção -d ou omita a opção e digite a data durante a execução do cadastro.")
    else:
        if (args.uti or args.isolamento or args.ocupacao):
            if (args.uti):
                updbalanco("txuti",args.registra,"pedir")
            if (args.isolamento):
                updbalanco("txisolamento",args.registra,"pedir")
            if (args.ocupacao):
                updbalanco("txocupacao",args.registra,"pedir")
        else:
            registra(args.registra,"pedir")
    
if args.balanco:
    if args.data:
        if validadata(args.data):
            balanco(args.balanco,args.data)
        else:
            print("Data informada inválida: utilize uma dáta válida, no passado para a opção -d ou omita a opção visualize os dados da data atual.")
    else:
        balanco(args.balanco)

if args.exclui:
    if args.data:
        if validadata(args.data):
            excluibalanco(args.exclui,args.data)
        else:
            print("Data informada inválida: utilize uma dáta válida, no passado para a opção -d ou omita a opção e digite a data durante a execução do cadastro.")
    else:
        excluibalanco(args.exclui)
