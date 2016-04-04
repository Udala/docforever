# Para importar las instancias iniciales de los codigos de hashes. El fichero testHashes.txt debe estar en la carpeta raiz, colgando de public 
# cualquiera@cualquiera-Lenovo-G50-70:~/AppEngine/google_appengine$ ./dev_appserver.py /home/cualquiera/Code3/BitcoinTransparency/BitTranspPrj/public/
# Ejecutar en http://127.0.0.1:8000/console, Interactive Console.
from model import Utxo

f = open('batch/inputs/testUtxoMain.txt', 'r')
for utxo in f:
    splitted=utxo.splitlines()[0].split(',')  # Quitamos el newline del final de cada linea
    if splitted!='':  # Por si hay lineas vacias
        Utxo.new(splitted[0],int(splitted[1]),int(splitted[2]),splitted[3]) 
