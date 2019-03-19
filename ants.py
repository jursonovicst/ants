#!/usr/bin/env python3

import argparse
from ants import Colony, Nest, Queen
import time
import multiprocessing

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='Ants', description="Ants load tester.")
    parser.add_argument('--listen', type=str, metavar='address', help="Master mode, listens for slave connections at.")
    parser.add_argument('--connect', type=str, nargs='+', metavar=('address', 'name'),
                        help="Slave mode, connects to master at 'address' with 'name' identifier.")
    parser.add_argument('--port', type=int, help='Port to use for connection (default: %(default)s)', default=7777)
    parser.add_argument('--nestcount', type=int, help='Number of nests to create per host (default: number of cores -2)'
                        , default=0)
    parser.add_argument('profile', type=argparse.FileType('r'), nargs='?',
                        help="Python file containing a subclass of the Queen class to describe the load profile.")

    args = parser.parse_args()

    mycolony = None
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
            if 'profile' not in args:
                raise AttributeError("Error, profile file most be defined for master mode!")

            print("master mode with ")
            mycolony = Colony(address=args.listen, port=args.port)
            time.sleep(1)

            # wait for nests to connect
            input("Connect slaves, then press enter to continue...")

            # continue to load

        else:
            if 'profile' not in args:
                raise AttributeError("Error, profile file most be defined for standalone mode!")

            print('standalone mode')
            mycolony = Colony(address='127.0.0.1', port=args.port)
            time.sleep(1)

            for i in range(0, (multiprocessing.cpu_count() - 2) if args.nestcount is 0 else args.nestcount):
                nest = Nest(address='127.0.0.1', port=args.port, name="%s_%d" % ('default', i))
                mynests.append(nest)
            time.sleep(1)

            # continue to load

        # load simulation Queen
        exec(args.profile.read())
        if len(Queen.__subclasses__()) != 1:
            raise SyntaxError("Profile file '%s' must contain exactly one subclass of Queen, found: %s" % (
                args.profile.name, list(map(lambda cls: cls.__name__, Queen.__subclasses__()))))

        # lay the eggs
        myqueen = Queen.__subclasses__()[0]()
        for egg in myqueen.layeggs():
            mycolony.addegg(egg)

        # execute simulation
        mycolony.execute()

        # wait till ends
        mycolony.join()

    except Exception as e:
        print(e)
        mycolony.terminate()
    except KeyboardInterrupt:
        print("interrupt")
        mycolony.terminate()

    finally:
        if mode != MMASTER:
            # wait for nests to terminate
            for nest in mynests:
                if nest.is_alive():
                    nest.join()
