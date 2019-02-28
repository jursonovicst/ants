#!python3

import argparse
from killthebeast import Colony, Nest
import time
import multiprocessing

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='colony', description='Colony load tester')
    parser.add_argument('--listen', type=str, metavar='address', help='Listen')
    parser.add_argument('--connect', type=str, nargs='+', metavar=('address', 'name'),
                        help='Connect to the Colony at address')
    parser.add_argument('--port', type=int, help='port to use (default: %(default)s)', default=7777)
    parser.add_argument('--nestcount', type=int, help='number of nests to create (default: number of cores -2)',
                        default=0)
    parser.add_argument('simfile', type=argparse.FileType('r'), nargs='?')
    args = parser.parse_args()

    mycolony = None
    mynests = []
    if args.connect is not None:
        print("slave mode")
        for i in range(0, (multiprocessing.cpu_count() - 2) if args.nestcount is 0 else args.nestcount):
            mynests.append(Nest(address=args.connect[0], port=args.port,
                                name="%s_%d" % (args.connect[1] if len(args.connect) > 1 else 'default', i)))
        exit(any(map(lambda nest: nest.exitcode, mynests)))

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


    def execute(colony: Colony):
        pass

    exec(args.simfile.read())
    execute(mycolony)

    # this will block
    mycolony.execute()
