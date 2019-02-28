#!python3

import argparse
from killthebeast import Colony, Nest
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='colony', description='Colony load tester')
    parser.add_argument('--listen', type=str, metavar='address', help='Listen')
    parser.add_argument('--connect', type=str, nargs='+', metavar=('address', 'name'),
                        help='Connect to the Colony at address')
    parser.add_argument('--port', type=int, help='port to use (default: %(default)s)', default=7777)
    parser.add_argument('simfile', type=argparse.FileType('r'), nargs='?')
    args = parser.parse_args()

    mycolony = None
    if args.connect is not None:
        print("slave mode")
        mynest = Nest(address=args.connect[0], port=args.port,
                      name=args.connect[1] if len(args.connect) > 1 else 'default')
        exit(mynest.exitcode)

    elif args.listen is not None:
        print("master mode")
        mycolony = Colony(address=args.listen, port=args.port)

        # wait for nests to connect
        input("Press Enter to continue...")
        # continue to load simulation

    else:
        print('standalone mode')
        mycolony = Colony(address='/tmp/colony.sock')
        time.sleep(1)
        mynest = Nest(address='/tmp/colony.sock')

        # continue to load simulation


    # import simulation file

    def execute(colony: Colony):
        pass


    exec(args.simfile.read())
    execute(mycolony)

    # this will block
    mycolony.execute()
