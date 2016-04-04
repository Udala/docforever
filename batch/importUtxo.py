#Interactive console

from model import Utxo

f = open('batch/inputs/testUtxoMain.txt', 'r')
for utxo in f:
    splitted=utxo.splitlines()[0].split(',')  # Quitamos el newline del final de cada linea
    if splitted!='':  # Por si hay lineas vacias
        Utxo.new(splitted[0],int(splitted[1]),int(splitted[2]),splitted[3]) 
