#!/usr/bin/env python3

import argparse
from ants import Colony, Nest, Queen
import time
import multiprocessing

# required packages:
# pycurl, lxml, numpy, chardet

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

    colony = None
    mynests = []

    MSTANDALONE = 0
    MMASTER = 1
    MSLAVE = 2
    mode = MSTANDALONE
    if args.connect is not None:
        mode = MSLAVE
    elif args.listen is not None:
        mode = MMASTER

    try:

        if mode == MSLAVE:
            print("slave mode")
            for i in range(0, (multiprocessing.cpu_count() - 2) if args.nestcount is 0 else args.nestcount):
                mynests.append(Nest(address=args.connect[0], port=args.port,
                                    name="%s_%d" % (args.connect[1] if len(args.connect) > 1 else 'default', i)))

            # wait till all ends
            for nest in mynests:
                if nest.is_alive():
                    nest.join()
            exit(0)

        elif mode == MMASTER:
            print("master mode")
            colony = Colony(address=args.listen, port=args.port)
            time.sleep(1)

            # wait for nests to connect
            input("Press Enter to load simulation...")

            # continue to load simulation

        else:
            print('standalone mode')
            colony = Colony(address='127.0.0.1', port=args.port)
            time.sleep(1)

            for i in range(0, (multiprocessing.cpu_count() - 2) if args.nestcount is 0 else args.nestcount):
                nest = Nest(address='127.0.0.1', port=args.port, name="%s_%d" % ('default', i))
                mynests.append(nest)
            time.sleep(1)

            # continue to load simulation

        # load simulation Queen
        exec(args.simfile.read())
        if len(Queen.__subclasses__()) != 1:
            raise SyntaxError("Simulation file '%s' must contain exactly one subclass of Queen, found: %s" % (
                args.simfile.name, list(map(lambda cls: cls.__name__, Queen.__subclasses__()))))

        # lay the eggs
        simqueen = Queen.__subclasses__()[0]()
        for egg in simqueen.layeggs():
            colony.addegg(egg)

        # execute simulation
        colony.execute()

        # wait till ends
        colony.join()

    except Exception as e:
        print(e)
        colony.terminate()
    except KeyboardInterrupt:
        print("interrupt")
        colony.terminate()

    finally:
        if mode != MMASTER:
            # wait for nests to terminate
            for nest in mynests:
                if nest.is_alive():
                    nest.join()
