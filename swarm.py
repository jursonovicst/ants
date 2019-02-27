#!python3

import argparse
from killthebeast import Colony, Nest, Egg, Ant, HTTPAnt, ABRAnt




if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='colony', description='Colony load tester')
    parser.add_argument('--listen',  type=str, nargs='+', metavar=('address', 'port'), help='Do not establish a local nest, just controll remote nests (default: %(default)s)', default=None)
    parser.add_argument('--connect', type=str, nargs='+', metavar=('address', 'port'), help='Connect to colony at address and port (default: %(default)s)', default=None)
    args = parser.parse_args()

    mycolony = None
    if args.listen is None and args.connect is None:
        print("Single mode")
        mycolony = Colony('/tmp/colony.sock')
        mynest = Nest('/tmp/colony.sock')

    else:
        if args.listen is not None:
            print("master mode")
            mycolony = Colony(args.listen[0],int(args.listen[1]))
        elif args.connect is not None:
            print("slave mode")
            mynest = Nest(args.connect[0],int(args.connect[1]))
        else:
            print("Incompatible mode")
            exit(1)

    import time
    time.sleep(5)

    mycolony.addegg(Egg(1, larv=Ant, name='1'))
#    mycolony.addegg(Egg(2, larv=HTTPAnt, name='2', server="www.bme.hu", paths=["/tom"], delays=[3]))
#    for i in range(3,100):
#        mycolony.addegg(Egg(i, larv=ABRAnt, name='%d' % i, manifest=""))

    mycolony.execute()
